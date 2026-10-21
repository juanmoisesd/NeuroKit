"""Base de datos y reglas de exclusión por defecto para Safe Debloat Manager.

Garantiza la protección de componentes críticos del sistema, controladores,
runtimes compartidos, Windows Update y herramientas de seguridad.
"""

from typing import Tuple, List
from .models import ItemCategory, SafetyLevel

# Paquetes y servicios del sistema operativo protegidos por defecto
SYSTEM_COMPONENT_PATTERNS = [
    "microsoft.windows.shellexperiencehost",
    "microsoft.windows.startmenuexperiencehost",
    "microsoft.windows.search",
    "microsoft.windows.cortana",
    "microsoft.windows.cloudexperiencehost",
    "microsoft.windows.contentdeliverymanager",
    "microsoft.windowsstore",
    "microsoft.windows.photos",  # Sensible para visores por defecto
    "microsoft.windows.parentalcontrols",
    "microsoft.windows.client.cbs",
    "microsoft.windows.oobenetworkconnection",
    "microsoft.windows.peopleexperiencehost",
    "microsoft.aad.brokerplugin",
    "microsoft.accountscontrol",
    "microsoft.bioenrollment",
    "microsoft.lockapp",
    "microsoft.win32webviewhost",
    "microsoft.windows.authhost",
    "microsoft.windows.capturepicker",
    "explorer.exe",
    "taskmgr.exe",
    "svchost.exe",
    "csrss.exe",
    "winlogon.exe",
    "services.exe",
    "lsass.exe",
    "dwm.exe",
    "ctfmon.exe",
]

# Controladores de hardware y librerías de fabricantes
DRIVER_PATTERNS = [
    "intel",
    "nvidia",
    "amd",
    "realtek",
    "synaptics",
    "qualcomm",
    "broadcom",
    "mediatek",
    "display link",
    "graphics driver",
    "audio driver",
    "chipset",
    "bluetooth",
    "wlan",
    "ethernet",
    "touchpad",
]

# Runtimes compartidos y entornos de ejecución requeridos por otras apps
RUNTIME_PATTERNS = [
    "microsoft visual c++",
    "vcredist",
    ".net framework",
    ".net desktop runtime",
    ".net core",
    "directx",
    "universal crt",
    "vc_redist",
    "openxr",
    "webassembly",
    "microsoft.vclibs",
    "microsoft.net.native.runtime",
    "microsoft.net.native.framework",
    "microsoft.ui.xaml",
]

# Herramientas de seguridad y protección del sistema
SECURITY_PATTERNS = [
    "windows defender",
    "securityhealth",
    "antivirus",
    "firewall",
    "smartscreen",
    "defender",
    "bitdefender",
    "kaspersky",
    "malwarebytes",
    "mcafee",
    "norton",
    "eset",
    "avast",
    "avg",
    "threat",
]

# Componentes núcleo de Windows Update
WINDOWS_UPDATE_PATTERNS = [
    "wuauserv",
    "delivery optimization",
    "dosvc",
    "windows update",
    "softwaredistribution\\download",
    "usosvc",
    "waasmedicsvc",
]

# Carpetas del sistema prohibidas para cualquier borrado masivo o directo
CRITICAL_SYSTEM_PATHS = [
    "c:\\",
    "c:\\windows",
    "c:\\windows\\system32",
    "c:\\windows\\syswow64",
    "c:\\program files",
    "c:\\program files (x86)",
    "c:\\users",
    "c:\\programdata",
]


def is_critical_system_path(path: str) -> bool:
    """Verifica si una ruta es un directorio crítico del sistema que nunca debe borrarse."""
    if not path:
        return False
    normalized = path.strip().lower().replace("/", "\\").rstrip("\\")
    for sys_path in CRITICAL_SYSTEM_PATHS:
        sys_norm = sys_path.lower().rstrip("\\")
        if normalized == sys_norm:
            return True
    return False


def evaluate_exclusion(
    category: ItemCategory,
    name: str,
    path_or_package: str,
    publisher: str = "",
) -> Tuple[bool, str, SafetyLevel]:
    """Evalúa si un elemento debe ser excluido por defecto por razones de seguridad.

    Retorna:
        Tuple[bool, str, SafetyLevel]: (es_excluido, motivo_exclusion, nivel_seguridad)
    """
    target = f"{name} {path_or_package} {publisher}".lower()

    # 1. Rutas del sistema crítico
    if is_critical_system_path(path_or_package):
        return True, "Directorio raíz crítico del sistema operativo", SafetyLevel.EXCLUDED

    # 2. Herramientas de seguridad
    for pat in SECURITY_PATTERNS:
        if pat in target:
            return True, f"Herramienta de seguridad o antivirus ({pat})", SafetyLevel.EXCLUDED

    # 3. Controladores de hardware
    for pat in DRIVER_PATTERNS:
        if pat in target:
            return True, f"Controlador de hardware o firmware ({pat})", SafetyLevel.EXCLUDED

    # 4. Runtimes compartidos
    for pat in RUNTIME_PATTERNS:
        if pat in target:
            return True, f"Runtime o librería compartida del sistema ({pat})", SafetyLevel.EXCLUDED

    # 5. Componentes esenciales del SO
    for pat in SYSTEM_COMPONENT_PATTERNS:
        if pat in target:
            return True, f"Componente esencial del sistema operativo ({pat})", SafetyLevel.EXCLUDED

    # 6. Windows Update (excepto caché temporal de descargas no esencial)
    for pat in WINDOWS_UPDATE_PATTERNS:
        if pat in target and "softwaredistribution" not in target:
            return True, f"Componente núcleo de Windows Update ({pat})", SafetyLevel.EXCLUDED

    # Si es archivo temporal seguro o app no de sistema
    if category == ItemCategory.SAFE_TEMP:
        return False, "Archivo temporal seguro de limpiar", SafetyLevel.SAFE

    # Para apps preinstaladas / inicio
    if "microsoft" in publisher.lower() and ("core" in target or "system" in target):
        return True, "Servicio o aplicación del sistema Microsoft", SafetyLevel.EXCLUDED

    return False, "Elemento estándar no crítico", SafetyLevel.SAFE
