"""Motor de escaneo de aplicaciones preinstaladas, programas de inicio y archivos temporales.

Soporta ejecución real en Windows 10 x64 mediante comandos PowerShell y Registro de Windows,
así como un modo de demostración/pruebas multiplataforma.
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .models import DebloatItem, ItemCategory, SafetyLevel, format_size
from .exclusions import evaluate_exclusion, is_critical_system_path


class DebloatScanner:
    """Escáner principal para Safe Debloat Manager."""

    def __init__(self, force_mock: bool = False):
        """Inicializa el escáner.

        Args:
            force_mock: Si es True, utiliza datos simulados independientemente del sistema operativo.
        """
        self.is_windows = platform.system().lower() == "windows" and not force_mock
        self.force_mock = force_mock

    def scan_all(self) -> List[DebloatItem]:
        """Ejecuta el escaneo completo de todas las categorías."""
        items: List[DebloatItem] = []
        items.extend(self.scan_preinstalled_apps())
        items.extend(self.scan_startup_apps())
        items.extend(self.scan_safe_temp_files())
        return items

    def scan_preinstalled_apps(self) -> List[DebloatItem]:
        """Escanea aplicaciones preinstaladas (AppX y bloatware)."""
        if self.is_windows:
            return self._scan_windows_appx()
        else:
            return self._get_mock_preinstalled_apps()

    def scan_startup_apps(self) -> List[DebloatItem]:
        """Escanea programas configurados para iniciarse automáticamente."""
        if self.is_windows:
            return self._scan_windows_startup()
        else:
            return self._get_mock_startup_apps()

    def scan_safe_temp_files(self) -> List[DebloatItem]:
        """Escanea rutas de archivos temporales seguros."""
        items: List[DebloatItem] = []
        temp_dirs = self._get_target_temp_directories()

        for cat_name, path, description, dependencies in temp_dirs:
            if not path or not os.path.exists(path):
                continue

            # Verificación estricta de seguridad de ruta
            if is_critical_system_path(path):
                continue

            size_bytes, file_count = self._calculate_dir_size(path)
            if size_bytes <= 0 and self.force_mock:
                size_bytes = 45 * 1024 * 1024
                file_count = 120

            if size_bytes <= 0:
                continue

            is_excluded, reason, safety = evaluate_exclusion(
                ItemCategory.SAFE_TEMP, cat_name, path, publisher="Microsoft Windows"
            )

            item_id = f"temp_{cat_name.lower().replace(' ', '_')}"
            item = DebloatItem(
                item_id=item_id,
                name=cat_name,
                category=ItemCategory.SAFE_TEMP,
                path_or_package=path,
                description=f"{description} ({file_count} archivos)",
                size_bytes=size_bytes,
                dependencies=dependencies,
                is_excluded_by_default=is_excluded,
                exclusion_reason=reason,
                recovery_command="N/A (Los archivos temporales se recrean automáticamente si la app los necesita)",
                is_selected=not is_excluded,
                safety_level=safety,
                publisher="Microsoft / Sistema",
                details={"file_count": file_count, "folder_path": path},
            )
            items.append(item)

        return items

    def _calculate_dir_size(self, folder_path: str) -> Tuple[int, int]:
        """Calcula el tamaño acumulado en bytes y la cantidad de archivos de una carpeta."""
        total_size = 0
        file_count = 0
        try:
            for root, _, files in os.walk(folder_path):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)
                            file_count += 1
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
        return total_size, file_count

    def _get_target_temp_directories(self) -> List[Tuple[str, str, str, str]]:
        """Retorna las rutas temporales seguras a analizar según el entorno."""
        temp_list = []

        # Temp de usuario
        user_temp = os.environ.get("TEMP") or os.environ.get("TMP")
        if user_temp and os.path.exists(user_temp):
            temp_list.append((
                "Caché Temporal de Usuario",
                user_temp,
                "Archivos temporales generados por aplicaciones en la sesión del usuario.",
                "Sin dependencias críticas. Las aplicaciones regeneran archivos necesarios."
            ))

        # Windows Temp
        windir = os.environ.get("WINDIR", "C:\\Windows")
        sys_temp = os.path.join(windir, "Temp")
        if os.path.exists(sys_temp):
            temp_list.append((
                "Archivos Temporales del Sistema",
                sys_temp,
                "Archivos de registro y caché del sistema operativo Windows.",
                "Sin dependencias activas."
            ))

        # Prefetch
        prefetch = os.path.join(windir, "Prefetch")
        if os.path.exists(prefetch):
            temp_list.append((
                "Caché de Prefetch de Windows",
                prefetch,
                "Datos de precarga para acelerar el inicio de aplicaciones.",
                "Windows reconstruirá el prefetch según el uso habitual del usuario."
            ))

        # WER Logs / CrashDumps
        wer_logs = os.path.join(windir, "Logs")
        if os.path.exists(wer_logs):
            temp_list.append((
                "Registros de Diagnóstico y Logs",
                wer_logs,
                "Historial de eventos de diagnóstico y registros de error de Windows.",
                "Información histórica. No afecta el funcionamiento del sistema."
            ))

        # Windows Update Download Cache
        wu_download = os.path.join(windir, "SoftwareDistribution", "Download")
        if os.path.exists(wu_download):
            temp_list.append((
                "Caché de Descargas de Windows Update",
                wu_download,
                "Archivos de actualización descargados ya instalados o en espera.",
                "Windows Update los descarga nuevamente si fuera necesario."
            ))

        # Si estamos en entorno de prueba (force_mock) o no Windows, aseguramos rutas simuladas
        if self.force_mock or not self.is_windows:
            mock_temp = os.path.join(os.getcwd(), ".mock_temp")
            os.makedirs(mock_temp, exist_ok=True)
            dummy_file = os.path.join(mock_temp, "dummy_cache.tmp")
            if not os.path.exists(dummy_file):
                with open(dummy_file, "w") as f:
                    f.write("X" * 1024 * 1024)
            temp_list.append((
                "Caché Temporal de Usuario (Simulado)",
                mock_temp,
                "Archivos temporales de prueba para entorno seguro.",
                "Sin dependencias."
            ))

        return temp_list

    def _scan_windows_appx(self) -> List[DebloatItem]:
        """Ejecuta PowerShell en Windows para obtener la lista de paquetes AppX."""
        items: List[DebloatItem] = []
        ps_cmd = (
            "Get-AppxPackage | Select-Name, PackageFullName, InstallLocation, PublisherId, IsFramework "
            "| ConvertTo-Json"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]
                for app in data:
                    name = app.get("Name", "")
                    pkg_fullname = app.get("PackageFullName", "")
                    install_loc = app.get("InstallLocation") or ""
                    is_framework = app.get("IsFramework", False)

                    if not name or is_framework:
                        continue

                    size = 0
                    if install_loc and os.path.exists(install_loc):
                        size, _ = self._calculate_dir_size(install_loc)

                    is_excluded, reason, safety = evaluate_exclusion(
                        ItemCategory.PREINSTALLED_APP, name, pkg_fullname, app.get("PublisherId", "")
                    )

                    rec_cmd = (
                        f'Add-AppxPackage -Register "{install_loc}\\AppxManifest.xml" -DisableDevelopmentMode'
                        if install_loc else f'Get-AppxPackage -AllUsers *{name}* | Foreach {{Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\\AppXManifest.xml"}}'
                    )

                    items.append(DebloatItem(
                        item_id=f"appx_{pkg_fullname}",
                        name=name.split(".")[-1] if "." in name else name,
                        category=ItemCategory.PREINSTALLED_APP,
                        path_or_package=pkg_fullname,
                        description=f"Aplicación AppX Universal Windows Platform ({name})",
                        size_bytes=size or 45 * 1024 * 1024,
                        dependencies="Otras aplicaciones UWP o servicios del sistema si es un runtime compartido.",
                        is_excluded_by_default=is_excluded,
                        exclusion_reason=reason,
                        recovery_command=rec_cmd,
                        is_selected=not is_excluded,
                        safety_level=safety,
                        publisher=app.get("PublisherId", "Microsoft Corporation"),
                        details={"PackageFullName": pkg_fullname, "InstallLocation": install_loc},
                    ))
        except Exception:
            items.extend(self._get_mock_preinstalled_apps())
        return items

    def _scan_windows_startup(self) -> List[DebloatItem]:
        """Escanea claves de registro e inicio de Windows."""
        items: List[DebloatItem] = []
        try:
            import winreg
            reg_locations = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run"),
            ]
            for hkey, subkey, label in reg_locations:
                try:
                    with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ) as key:
                        idx = 0
                        while True:
                            try:
                                name, val, _ = winreg.EnumValue(key, idx)
                                path = str(val).split('"')[1] if '"' in str(val) else str(val).split()[0]
                                size = os.path.getsize(path) if os.path.exists(path) else 1024 * 500

                                is_excluded, reason, safety = evaluate_exclusion(
                                    ItemCategory.STARTUP_APP, name, path, label
                                )

                                items.append(DebloatItem(
                                    item_id=f"startup_{label}_{name}",
                                    name=name,
                                    category=ItemCategory.STARTUP_APP,
                                    path_or_package=path,
                                    description=f"Programa de inicio automático registrado en {label}",
                                    size_bytes=size,
                                    dependencies="Servicios o características asociadas al programa.",
                                    is_excluded_by_default=is_excluded,
                                    exclusion_reason=reason,
                                    recovery_command=f"Recrear clave de registro en {label}: {name} -> {val}",
                                    is_selected=not is_excluded,
                                    safety_level=safety,
                                    publisher="Terceros / Sistema",
                                    details={"reg_key": subkey, "reg_value_name": name, "raw_command": val},
                                ))
                                idx += 1
                            except OSError:
                                break
                except OSError:
                    continue
        except ImportError:
            items.extend(self._get_mock_startup_apps())
        return items

    def _get_mock_preinstalled_apps(self) -> List[DebloatItem]:
        """Proporciona datos simulados para pruebas y demostración."""
        mock_apps = [
            ("Microsoft.CandyCrushSaga", "Candy Crush Saga", 250 * 1024 * 1024, "Juego preinstalado publicitario", "Ninguna dependencias conocida", False, "Juego de terceros opcional"),
            ("Microsoft.BingNews", "Noticias de MSN", 85 * 1024 * 1024, "Aplicación de noticias e información", "Widget de noticias de la barra de tareas", False, "Aplicación informativa opcional"),
            ("Microsoft.XboxApp", "Xbox App", 120 * 1024 * 1024, "Plataforma de juegos Xbox para Windows", "Xbox Live Services", False, "Complemento para juegos"),
            ("Microsoft.WindowsFeedbackHub", "Centro de Comentarios", 45 * 1024 * 1024, "Envío de comentarios a Microsoft", "Servicio de diagnóstico", False, "Herramienta de retroalimentación"),
            ("Microsoft.SkypeApp", "Skype", 180 * 1024 * 1024, "Cliente de comunicación y videollamadas", "Ninguna", False, "Aplicación de mensajería opcional"),
            ("Microsoft.WindowsDefender", "Windows Defender Security Center", 350 * 1024 * 1024, "Antivirus y centro de seguridad nativo de Windows", "Servicios de seguridad en tiempo real y Firewall", True, "Herramienta de seguridad crítica del sistema"),
            ("Microsoft.VCLibs.140.00", "Microsoft Visual C++ Runtime Package", 65 * 1024 * 1024, "Librerías C++ compartidas para aplicaciones UWP", "Decenas de aplicaciones UWP dependen de este paquete", True, "Runtime compartido esencial para otras aplicaciones"),
            ("Microsoft.Windows.ShellExperienceHost", "Windows Shell Experience Host", 90 * 1024 * 1024, "Interfaz gráfica del menú Inicio y barra de tareas", "Explorador de Windows y menú Inicio", True, "Componente esencial del sistema operativo"),
        ]

        items = []
        for pkg_id, name, size, desc, deps, default_excluded, reason in mock_apps:
            is_exc, exc_reason, safety = evaluate_exclusion(
                ItemCategory.PREINSTALLED_APP, name, pkg_id, "Microsoft Corporation"
            )
            final_exc = default_excluded or is_exc
            final_reason = reason if default_excluded else exc_reason

            items.append(DebloatItem(
                item_id=f"appx_{pkg_id}",
                name=name,
                category=ItemCategory.PREINSTALLED_APP,
                path_or_package=pkg_id,
                description=desc,
                size_bytes=size,
                dependencies=deps,
                is_excluded_by_default=final_exc,
                exclusion_reason=final_reason,
                recovery_command=f'Get-AppxPackage -AllUsers *{name}* | Foreach {{Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\\AppXManifest.xml"}}',
                is_selected=not final_exc,
                safety_level=SafetyLevel.EXCLUDED if final_exc else SafetyLevel.SAFE,
                publisher="Microsoft Corporation",
                details={"PackageFullName": pkg_id},
            ))
        return items

    def _get_mock_startup_apps(self) -> List[DebloatItem]:
        """Proporciona datos simulados de inicio para pruebas."""
        mock_startup = [
            ("Spotify", "C:\\Users\\Usuario\\AppData\\Roaming\\Spotify\\Spotify.exe", 140 * 1024 * 1024, "Reproductor de música Spotify", "Ninguna dependencias requerida al inicio", False, "Programa de terceros opcional"),
            ("OneDrive", "C:\\Users\\Usuario\\AppData\\Local\\Microsoft\\OneDrive\\OneDrive.exe", 110 * 1024 * 1024, "Cliente de sincronización en la nube Microsoft OneDrive", "Sincronización de carpetas personales", False, "Servicio de almacenamiento opcional"),
            ("RealtekAudioConsole", "C:\\Program Files\\Realtek\\Audio\\RtkAudioService.exe", 45 * 1024 * 1024, "Panel de control del chip de sonido Realtek", "Controlador de audio del sistema", True, "Controlador de hardware de audio"),
            ("SecurityHealthTray", "C:\\Windows\\System32\\SecurityHealthSystray.exe", 15 * 1024 * 1024, "Icono de estado de seguridad en la barra de tareas", "Windows Defender Security Center", True, "Herramienta de seguridad del sistema"),
        ]

        items = []
        for name, path, size, desc, deps, default_excluded, reason in mock_startup:
            is_exc, exc_reason, safety = evaluate_exclusion(
                ItemCategory.STARTUP_APP, name, path, "Microsoft / Vendor"
            )
            final_exc = default_excluded or is_exc
            final_reason = reason if default_excluded else exc_reason

            items.append(DebloatItem(
                item_id=f"startup_HKCU_{name}",
                name=name,
                category=ItemCategory.STARTUP_APP,
                path_or_package=path,
                description=desc,
                size_bytes=size,
                dependencies=deps,
                is_excluded_by_default=final_exc,
                exclusion_reason=final_reason,
                recovery_command=f"Restaurar entrada en HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run -> {name} = '{path}'",
                is_selected=not final_exc,
                safety_level=SafetyLevel.EXCLUDED if final_exc else SafetyLevel.SAFE,
                publisher="Vendor",
                details={"reg_key": r"Software\Microsoft\Windows\CurrentVersion\Run", "reg_value_name": name},
            ))
        return items
