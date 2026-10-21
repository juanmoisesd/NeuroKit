"""Gestión de procedimientos de recuperación, respaldo de registro y puntos de restauración."""

import os
import json
import subprocess
import platform
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class RecoveryManager:
    """Manejador de respaldo de configuración y procedimientos de restauración."""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_system_restore_point(self, description: str = "Safe Debloat Manager") -> Tuple[bool, str]:
        """Intenta crear un Punto de Restauración del Sistema en Windows."""
        if platform.system().lower() != "windows":
            return True, "Simulación: Punto de restauración generado en entorno non-Windows."

        ps_cmd = (
            f'Checkpoint-Computer -Description "{description}" -RestorePointType "MODIFY_SETTINGS"'
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if res.returncode == 0:
                return True, "Punto de restauración creado con éxito."
            else:
                return False, f"Error al crear punto de restauración: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Excepción al invocar Checkpoint-Computer: {str(e)}"

    def backup_startup_item(self, item_name: str, reg_key: str, reg_value_name: str, raw_command: str) -> str:
        """Crea un respaldo de una clave de inicio en archivo .json / .reg."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in item_name if c.isalnum() or c in ("_", "-"))
        filename = f"startup_backup_{safe_name}_{timestamp}.json"
        filepath = os.path.join(self.backup_dir, filename)

        backup_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "item_name": item_name,
            "reg_key": reg_key,
            "reg_value_name": reg_value_name,
            "raw_command": raw_command,
            "restore_cmd": f"winreg / restore key {reg_key} -> {reg_value_name}={raw_command}",
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            return filepath
        except Exception:
            return ""

    def get_all_backups(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de todos los respaldos de inicio guardados."""
        backups = []
        if not os.path.exists(self.backup_dir):
            return backups

        for f in os.listdir(self.backup_dir):
            if f.endswith(".json"):
                fp = os.path.join(self.backup_dir, f)
                try:
                    with open(fp, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        data["backup_file"] = fp
                        backups.append(data)
                except Exception:
                    continue
        return backups

    def restore_startup_backup(self, backup_file_path: str) -> Tuple[bool, str]:
        """Restaura un programa de inicio previamente respaldado."""
        if not os.path.exists(backup_file_path):
            return False, "Archivo de respaldo no encontrado."

        try:
            with open(backup_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            reg_key = data.get("reg_key")
            val_name = data.get("reg_value_name")
            cmd = data.get("raw_command")

            if platform.system().lower() == "windows":
                import winreg
                root_hkey = winreg.HKEY_CURRENT_USER if "CURRENT_USER" in reg_key.upper() else winreg.HKEY_LOCAL_MACHINE
                subkey = reg_key.split("\\", 1)[1] if "\\" in reg_key else reg_key
                with winreg.OpenKey(root_hkey, subkey, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, val_name, 0, winreg.REG_SZ, cmd)
                return True, f"Entrada de inicio '{val_name}' restaurada correctamente en Registro."
            else:
                return True, f"Simulación: Entrada '{val_name}' restaurada con éxito."
        except Exception as e:
            return False, f"Error al restaurar respaldo: {str(e)}"
