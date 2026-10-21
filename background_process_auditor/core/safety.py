"""
Module: Safety Guardrails
Ensures critical system processes and security services in Windows 10 x64
cannot be terminated or disabled.
"""

from typing import Optional, Set

# Critical system processes on Windows that must NEVER be terminated
CRITICAL_PROCESS_NAMES: Set[str] = {
    "system",
    "system idle process",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "winlogon.exe",
    "services.exe",
    "lsass.exe",
    "svchost.exe",
    "fontdrvhost.exe",
    "wuauclt.exe",
    "explorer.exe",
    "taskmgr.exe",
    "sihost.exe",
    "dwminit.exe",
    "dwm.exe",
    "ctfmon.exe",
    "spoolsv.exe",
    "runtimebroker.exe",
    "searchindexer.exe",
    "securityhealthservice.exe",
    "smartscreen.exe",
    "msascuil.exe",
}

# Critical security services & applications that must NEVER be deactivated or terminated
CRITICAL_SECURITY_SERVICES: Set[str] = {
    "windefend",
    "mpssvc",
    "wscsvc",
    "sense",
    "securityhealthservice",
    "wuauserv",
    "bits",
    "trustedinstaller",
    "msmpsvc",
    "nissrv",
    "avp",
    "mbam",
    "avg",
    "avast",
    "bitdefender",
    "mcafee",
    "kaspersky",
    "norton",
    "eset",
    "windows security",
    "windows defender",
    "msascuil",
}

class SafetyGuard:
    """Provides safeguards to protect essential system operations and security tools."""

    @staticmethod
    def _normalize(name: str) -> str:
        return (name or "").strip().lower()

    @classmethod
    def is_critical_process(cls, process_name: str, pid: Optional[int] = None) -> bool:
        """
        Determines if a process is a critical system process.
        PIDs 0 and 4 are always System / System Idle on Windows.
        """
        if pid in (0, 4):
            return True

        norm_name = cls._normalize(process_name)
        if norm_name in CRITICAL_PROCESS_NAMES:
            return True

        # Check for matching without .exe extension
        name_no_ext = norm_name.replace(".exe", "")
        for crit in CRITICAL_PROCESS_NAMES:
            if crit.replace(".exe", "") == name_no_ext:
                return True

        return False

    @classmethod
    def is_security_service(cls, service_name_or_path: str) -> bool:
        """Determines if a service name or command line corresponds to a security tool."""
        norm_str = cls._normalize(service_name_or_path)
        for sec_term in CRITICAL_SECURITY_SERVICES:
            if sec_term in norm_str:
                return True
        return False

    @classmethod
    def can_terminate(cls, process_name: str, pid: Optional[int] = None) -> bool:
        """
        Returns True if the process is safe to terminate, False if it is protected.
        """
        if cls.is_critical_process(process_name, pid):
            return False
        if cls.is_security_service(process_name):
            return False
        return True

    @classmethod
    def can_disable_startup(cls, item_name: str, command: str) -> bool:
        """
        Returns True if a startup item can be safely disabled, False if protected.
        """
        if cls.is_critical_process(item_name) or cls.is_critical_process(command):
            return False
        if cls.is_security_service(item_name) or cls.is_security_service(command):
            return False
        return True
