"""Modelos de datos para Safe Debloat Manager."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional


class ItemCategory(str, Enum):
    """Categorías de elementos analizables."""
    PREINSTALLED_APP = "Aplicaciones Preinstaladas"
    STARTUP_APP = "Aplicaciones de Inicio"
    SAFE_TEMP = "Archivos Temporales Seguros"


class SafetyLevel(str, Enum):
    """Nivel de seguridad recomendado."""
    SAFE = "Seguro"
    CAUTION = "Precaución"
    EXCLUDED = "Excluido por Defecto"


def format_size(size_bytes: int) -> str:
    """Formatea bytes a representación legible (KB, MB, GB)."""
    if size_bytes < 0:
        return "0 B"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


@dataclass
class DebloatItem:
    """Representa un elemento identificable dentro del sistema."""
    item_id: str
    name: str
    category: ItemCategory
    path_or_package: str
    description: str
    size_bytes: int
    dependencies: str
    is_excluded_by_default: bool = False
    exclusion_reason: str = ""
    recovery_command: str = ""
    is_selected: bool = False
    safety_level: SafetyLevel = SafetyLevel.SAFE
    publisher: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def formatted_size(self) -> str:
        """Devuelve el tamaño formateado."""
        return format_size(self.size_bytes)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el elemento a un diccionario."""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "category": self.category.value if isinstance(self.category, ItemCategory) else str(self.category),
            "path_or_package": self.path_or_package,
            "description": self.description,
            "size_bytes": self.size_bytes,
            "formatted_size": self.formatted_size,
            "dependencies": self.dependencies,
            "is_excluded_by_default": self.is_excluded_by_default,
            "exclusion_reason": self.exclusion_reason,
            "recovery_command": self.recovery_command,
            "is_selected": self.is_selected,
            "safety_level": self.safety_level.value if isinstance(self.safety_level, SafetyLevel) else str(self.safety_level),
            "publisher": self.publisher,
            "details": self.details,
        }
