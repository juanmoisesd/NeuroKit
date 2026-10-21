"""Sistema de registro de acciones (logging) para Safe Debloat Manager."""

import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional


class ActionLogRecord:
    """Registro individual de acción."""

    def __init__(
        self,
        item_id: str,
        item_name: str,
        category: str,
        action_type: str,  # SIMULACION, ELIMINACION, PUNTO_RESTAURACION, BACKUP
        status: str,        # EXITO, ERROR, OMITIDO
        freed_bytes: int = 0,
        message: str = "",
    ):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.item_id = item_id
        self.item_name = item_name
        self.category = category
        self.action_type = action_type
        self.status = status
        self.freed_bytes = freed_bytes
        self.message = message

    def to_string(self) -> str:
        """Formatea el registro para visualización en texto."""
        freed_str = f" [{self.freed_bytes / (1024*1024):.2f} MB liberados]" if self.freed_bytes > 0 else ""
        return f"[{self.timestamp}] [{self.action_type}] [{self.status}] {self.category} - {self.item_name}{freed_str}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            "timestamp": self.timestamp,
            "item_id": self.item_id,
            "item_name": self.item_name,
            "category": self.category,
            "action_type": self.action_type,
            "status": self.status,
            "freed_bytes": self.freed_bytes,
            "message": self.message,
        }


class ActionLogger:
    """Manejador global de registros de auditoría y acciones."""

    def __init__(self, log_file_path: str = "debloat_actions.log"):
        self.log_file_path = log_file_path
        self.records: List[ActionLogRecord] = []

    def log_action(
        self,
        item_id: str,
        item_name: str,
        category: str,
        action_type: str,
        status: str,
        freed_bytes: int = 0,
        message: str = "",
    ) -> ActionLogRecord:
        """Registra una acción tanto en memoria como en el archivo de registro."""
        rec = ActionLogRecord(
            item_id=item_id,
            item_name=item_name,
            category=category,
            action_type=action_type,
            status=status,
            freed_bytes=freed_bytes,
            message=message,
        )
        self.records.append(rec)
        self.append_to_file(rec.to_string())
        return rec

    def append_to_file(self, line: str) -> None:
        """Escribe una línea en el archivo de logs."""
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def get_all_records(self) -> List[ActionLogRecord]:
        """Devuelve todos los registros guardados en la sesión actual."""
        return self.records

    def export_log(self, target_path: str) -> bool:
        """Exporta todo el historial a un archivo especificado."""
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write("=== REGISTRO DE ACCIONES DE SAFE DEBLOAT MANAGER ===\n")
                f.write(f"Fecha de informe: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for r in self.records:
                    f.write(r.to_string() + "\n")
            return True
        except Exception:
            return False
