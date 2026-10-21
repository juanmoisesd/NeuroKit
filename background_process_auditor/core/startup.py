"""
Module: Startup Application Manager
Manages Windows startup applications (Registry HKCU/HKLM, Startup folder),
maintains backup configurations before changes, and allows safe restoration.
"""

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from background_process_auditor.core.safety import SafetyGuard


@dataclass
class StartupItem:
    id: str
    name: str
    command: str
    location: str  # HKCU_Run, HKLM_Run, Startup_Folder, etc.
    enabled: bool
    is_essential: bool
    status_reason: str = ""


class StartupManager:
    """Manages Windows startup items, state backups, and safe toggle operations."""

    def __init__(self, backup_dir: Optional[str] = None) -> None:
        if backup_dir is None:
            backup_dir = os.path.join(os.path.expanduser("~"), ".bg_process_auditor", "startup_backups")
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)
        self.state_file = os.path.join(self.backup_dir, "current_state.json")
        self.items: Dict[str, StartupItem] = {}
        self._disabled_cache: Dict[str, StartupItem] = self._load_state_file()

    def _load_state_file(self) -> Dict[str, StartupItem]:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {k: StartupItem(**v) for k, v in data.items()}
            except Exception:
                pass
        return {}

    def _save_state_file(self) -> None:
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump({k: asdict(v) for k, v in self.items.items()}, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def scan_startup_items(self) -> List[StartupItem]:
        """
        Scans current startup applications. Uses winreg on Windows or mock items
        for testing / non-Windows environments.
        """
        scanned: List[StartupItem] = []

        if sys.platform == "win32":
            try:
                import winreg

                # HKCU Run
                scanned.extend(self._scan_registry_key(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU_Run"))
                # HKLM Run
                scanned.extend(self._scan_registry_key(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM_Run"))
            except Exception:
                pass

        # If no items scanned (e.g. non-Windows environment or no registry entries), provide standard mock/test items
        if not scanned:
            scanned = self._get_default_mock_items()

        # Merge with stored states (for items marked disabled)
        self.items = {}
        for item in scanned:
            if item.id in self._disabled_cache:
                item.enabled = self._disabled_cache[item.id].enabled
            self.items[item.id] = item

        # Also include items that were disabled previously and thus removed from actual Run key
        for item_id, item in self._disabled_cache.items():
            if item_id not in self.items and not item.enabled:
                self.items[item_id] = item

        return list(self.items.values())

    def _scan_registry_key(self, root_key, subkey_path: str, location_label: str) -> List[StartupItem]:
        items = []
        try:
            import winreg
            key = winreg.OpenKey(root_key, subkey_path, 0, winreg.KEY_READ)
            index = 0
            while True:
                try:
                    name, val, _ = winreg.EnumValue(key, index)
                    item_id = f"{location_label}::{name}"
                    is_ess = not SafetyGuard.can_disable_startup(name, val)
                    reason = "Proceso o Servicio Crítico del Sistema / Seguridad" if is_ess else "Aplicación de Terceros"
                    items.append(
                        StartupItem(
                            id=item_id,
                            name=name,
                            command=str(val),
                            location=location_label,
                            enabled=True,
                            is_essential=is_ess,
                            status_reason=reason,
                        )
                    )
                    index += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass
        return items

    def _get_default_mock_items(self) -> List[StartupItem]:
        mock_data = [
            ("sys_defender", "Windows Defender Security", "C:\\Program Files\\Windows Defender\\MSASCuiL.exe", "HKLM_Run", True),
            ("sys_audio", "Realtek HD Audio Universal Service", "RtkAudioService.exe", "HKLM_Run", False),
            ("app_discord", "Discord", "C:\\Users\\User\\AppData\\Local\\Discord\\Update.exe --processStart Discord.exe", "HKCU_Run", False),
            ("app_steam", "Steam Client Bootstrapper", "C:\\Program Files (x86)\\Steam\\steam.exe -silent", "HKCU_Run", False),
            ("app_cloud", "CloudSyncAgent", "C:\\Program Files\\CloudSync\\sync.exe --background", "HKCU_Run", False),
        ]
        items = []
        for item_id, name, cmd, loc, is_sec in mock_data:
            is_ess = is_sec or not SafetyGuard.can_disable_startup(name, cmd)
            reason = "Protección de Seguridad / Sistema Operativo" if is_ess else "Aplicación de Inicio No Esencial"
            items.append(
                StartupItem(
                    id=item_id,
                    name=name,
                    command=cmd,
                    location=loc,
                    enabled=True,
                    is_essential=is_ess,
                    status_reason=reason,
                )
            )
        return items

    def save_backup(self) -> str:
        """Saves current startup configuration state to a JSON backup file."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"startup_backup_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        backup_data = {item_id: asdict(item) for item_id, item in self.items.items()}
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        return backup_path

    def list_backups(self) -> List[str]:
        """Returns list of available backup file paths ordered by newest first."""
        if not os.path.exists(self.backup_dir):
            return []
        files = [os.path.join(self.backup_dir, f) for f in os.listdir(self.backup_dir) if f.startswith("startup_backup_") and f.endswith(".json")]
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return files

    def restore_backup(self, backup_path: Optional[str] = None) -> bool:
        """Restores startup application configuration from a backup file."""
        if not backup_path:
            backups = self.list_backups()
            if not backups:
                return False
            backup_path = backups[0]

        if not os.path.exists(backup_path):
            return False

        with open(backup_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item_id, item_dict in data.items():
            item = StartupItem(**item_dict)
            self.items[item_id] = item
            if sys.platform == "win32":
                self._apply_registry_change(item, item.enabled)

        self._disabled_cache = dict(self.items)
        self._save_state_file()
        return True

    def _apply_registry_change(self, item: StartupItem, enable: bool) -> None:
        if sys.platform != "win32":
            return
        try:
            import winreg
            root = winreg.HKEY_CURRENT_USER if item.location.startswith("HKCU") else winreg.HKEY_LOCAL_MACHINE
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(root, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
            if enable:
                winreg.SetValueEx(key, item.name, 0, winreg.REG_SZ, item.command)
            else:
                try:
                    winreg.DeleteValue(key, item.name)
                except OSError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass

    def toggle_item(self, item_id: str, enable: bool) -> tuple[bool, str]:
        """
        Enables or disables a startup item safely.
        Never allows disabling essential security services or system processes.
        """
        item = self.items.get(item_id)
        if not item:
            return False, "Aplicación de inicio no encontrada."

        if not enable and item.is_essential:
            return False, f"Acción denegada: '{item.name}' es una aplicación o servicio esencial del sistema/seguridad."

        if not enable and not SafetyGuard.can_disable_startup(item.name, item.command):
            return False, f"Acción denegada por directivas de seguridad para '{item.name}'."

        # Create automatic backup before changing state
        self.save_backup()
        item.enabled = enable
        if sys.platform == "win32":
            self._apply_registry_change(item, enable)

        self._disabled_cache[item_id] = item
        self._save_state_file()

        return True, f"Estado de '{item.name}' actualizado correctamente a {'Habilitado' if enable else 'Deshabilitado'}."
