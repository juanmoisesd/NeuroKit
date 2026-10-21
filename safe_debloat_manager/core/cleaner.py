"""Motor de eliminación segura, simulación y limpieza del sistema."""

import os
import shutil
import platform
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

from .models import DebloatItem, ItemCategory, format_size
from .exclusions import is_critical_system_path
from .logger import ActionLogger
from .recovery import RecoveryManager


@dataclass
class CleanerResult:
    """Resultado del proceso de limpieza o simulación."""
    total_processed: int
    successful: int
    failed: int
    skipped: int
    bytes_freed: int
    simulation_mode: bool
    summary_messages: List[str]


class DebloatCleaner:
    """Motor de ejecución de acciones de limpieza con salvaguardas."""

    def __init__(
        self,
        logger: Optional[ActionLogger] = None,
        recovery_mgr: Optional[RecoveryManager] = None,
    ):
        self.logger = logger or ActionLogger()
        self.recovery_mgr = recovery_mgr or RecoveryManager()

    def execute_cleaning(
        self,
        items: List[DebloatItem],
        simulation_mode: bool = True,
        create_restore_point: bool = False,
    ) -> CleanerResult:
        """Ejecuta la eliminación o la simulación de los elementos seleccionados.

        Args:
            items: Lista de elementos seleccionados a procesar.
            simulation_mode: Si es True, no aplica cambios reales y solo simula.
            create_restore_point: Si es True, solicita la creación de un punto de restauración.

        Returns:
            CleanerResult: Informe resumido de la ejecución.
        """
        successful = 0
        failed = 0
        skipped = 0
        bytes_freed = 0
        summary_messages: List[str] = []

        selected_items = [item for item in items if item.is_selected]

        if not selected_items:
            return CleanerResult(
                total_processed=0,
                successful=0,
                failed=0,
                skipped=0,
                bytes_freed=0,
                simulation_mode=simulation_mode,
                summary_messages=["No hay elementos seleccionados para procesar."],
            )

        # 1. Punto de restauración previa
        if create_restore_point:
            rp_ok, rp_msg = self.recovery_mgr.create_system_restore_point()
            action_label = "SIMULACION" if simulation_mode else "PUNTO_RESTAURACION"
            self.logger.log_action(
                item_id="restore_point",
                item_name="Punto de Restauración",
                category="Sistema",
                action_type=action_label,
                status="EXITO" if rp_ok else "ERROR",
                message=rp_msg,
            )
            summary_messages.append(f"Punto de restauración: {rp_msg}")

        # 2. Procesamiento de elementos
        for item in selected_items:
            if simulation_mode:
                ok, freed, msg = self._simulate_item_removal(item)
                action_str = "SIMULACION"
            else:
                ok, freed, msg = self._remove_item_real(item)
                action_str = "ELIMINACION"

            if ok:
                successful += 1
                bytes_freed += freed
                status_str = "EXITO"
            else:
                failed += 1
                status_str = "ERROR"

            self.logger.log_action(
                item_id=item.item_id,
                item_name=item.name,
                category=item.category.value if isinstance(item.category, ItemCategory) else str(item.category),
                action_type=action_str,
                status=status_str,
                freed_bytes=freed,
                message=msg,
            )

        mode_str = "Simulación completada" if simulation_mode else "Limpieza completada"
        summary_messages.append(
            f"{mode_str}: {successful} procesados correctamente, {failed} fallidos. "
            f"Espacio total liberado: {format_size(bytes_freed)}"
        )

        return CleanerResult(
            total_processed=len(selected_items),
            successful=successful,
            failed=failed,
            skipped=skipped,
            bytes_freed=bytes_freed,
            simulation_mode=simulation_mode,
            summary_messages=summary_messages,
        )

    def _simulate_item_removal(self, item: DebloatItem) -> Tuple[bool, int, str]:
        """Simula la eliminación de un elemento."""
        # Verificación estricta de ruta crítica del sistema
        if is_critical_system_path(item.path_or_package):
            return False, 0, f"Cancelado: {item.path_or_package} es un directorio del sistema protegido."

        if item.category == ItemCategory.PREINSTALLED_APP:
            msg = f"Simulación: Se desinstalaría el paquete AppX '{item.path_or_package}'"
            return True, item.size_bytes, msg

        elif item.category == ItemCategory.STARTUP_APP:
            msg = f"Simulación: Se respaldaría y deshabilitaría el inicio automático para '{item.name}' ({item.path_or_package})"
            return True, item.size_bytes, msg

        elif item.category == ItemCategory.SAFE_TEMP:
            msg = f"Simulación: Se vaciarían los archivos contenidos en '{item.path_or_package}'"
            return True, item.size_bytes, msg

        return False, 0, "Categoría desconocida."

    def _remove_item_real(self, item: DebloatItem) -> Tuple[bool, int, str]:
        """Ejecuta la eliminación real de un elemento respetando las salvaguardas."""
        # Protección absoluta contra borrado de carpetas del sistema
        if is_critical_system_path(item.path_or_package):
            return False, 0, f"ACCION BLOQUEADA POR SEGURIDAD: Ruta protegida del sistema '{item.path_or_package}'"

        if item.category == ItemCategory.PREINSTALLED_APP:
            return self._remove_appx_package(item)

        elif item.category == ItemCategory.STARTUP_APP:
            return self._disable_startup_item(item)

        elif item.category == ItemCategory.SAFE_TEMP:
            return self._clean_temp_directory(item)

        return False, 0, "Categoría no soportada para borrado real."

    def _remove_appx_package(self, item: DebloatItem) -> Tuple[bool, int, str]:
        """Elimina un paquete AppX mediante PowerShell."""
        if platform.system().lower() != "windows":
            return True, item.size_bytes, f"Simulación (Entorno Non-Windows): AppX '{item.name}' eliminado."

        pkg_name = item.path_or_package
        ps_cmd = f"Remove-AppxPackage -Package '{pkg_name}'"
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=20,
            )
            if res.returncode == 0:
                return True, item.size_bytes, f"Paquete AppX '{item.name}' eliminado correctamente."
            else:
                err = res.stderr.strip() or res.stdout.strip()
                return False, 0, f"Error de PowerShell al eliminar '{item.name}': {err}"
        except Exception as e:
            return False, 0, f"Excepción al ejecutar Remove-AppxPackage: {str(e)}"

    def _disable_startup_item(self, item: DebloatItem) -> Tuple[bool, int, str]:
        """Deshabilita una entrada de inicio respaldando su clave previa."""
        reg_key = item.details.get("reg_key", r"Software\Microsoft\Windows\CurrentVersion\Run")
        val_name = item.details.get("reg_value_name", item.name)
        raw_cmd = item.details.get("raw_command", item.path_or_package)

        # Crear respaldo previo
        backup_file = self.recovery_mgr.backup_startup_item(item.name, reg_key, val_name, raw_cmd)

        if platform.system().lower() != "windows":
            return True, item.size_bytes, f"Simulación: Inicio de '{item.name}' deshabilitado. Respaldo en {backup_file}"

        try:
            import winreg
            root_hkey = winreg.HKEY_CURRENT_USER if "CURRENT_USER" in reg_key.upper() else winreg.HKEY_LOCAL_MACHINE
            subkey = reg_key.split("\\", 1)[1] if "\\" in reg_key else reg_key

            with winreg.OpenKey(root_hkey, subkey, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, val_name)

            return True, item.size_bytes, f"Programa de inicio '{item.name}' eliminado. Respaldo guardado en {os.path.basename(backup_file)}"
        except Exception as e:
            return False, 0, f"Error al eliminar clave de registro de inicio: {str(e)}"

    def _clean_temp_directory(self, item: DebloatItem) -> Tuple[bool, int, str]:
        """Limpia los archivos de una carpeta temporal sin eliminar la carpeta raíz."""
        dir_path = item.path_or_package

        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            return False, 0, f"La carpeta '{dir_path}' no existe o no es válida."

        if is_critical_system_path(dir_path):
            return False, 0, f"ACCION BLOQUEADA: Imposible limpiar carpeta del sistema '{dir_path}'."

        deleted_files = 0
        freed_bytes = 0

        # Borrado seguro elemento por elemento dentro del directorio objetivo
        try:
            for entry in os.scandir(dir_path):
                try:
                    if entry.is_file(follow_symlinks=False) or entry.is_symlink():
                        file_size = entry.stat().st_size
                        os.unlink(entry.path)
                        freed_bytes += file_size
                        deleted_files += 1
                    elif entry.is_dir(follow_symlinks=False):
                        dir_size = self._get_folder_size(entry.path)
                        shutil.rmtree(entry.path, ignore_errors=True)
                        freed_bytes += dir_size
                        deleted_files += 1
                except (PermissionError, OSError):
                    # Ignorar archivos bloqueados o en uso por el sistema
                    continue
            return True, freed_bytes, f"Limpieza temporal completada ({deleted_files} elementos eliminados, {format_size(freed_bytes)} liberados)."
        except Exception as e:
            return False, freed_bytes, f"Error durante la limpieza temporal: {str(e)}"

    def _get_folder_size(self, path: str) -> int:
        """Calcula el tamaño acumulado de una subcarpeta."""
        total = 0
        try:
            for root, _, files in os.walk(path):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        total += os.path.getsize(fp)
                    except OSError:
                        pass
        except OSError:
            pass
        return total
