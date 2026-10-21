"""
Unit tests for Safety Safeguards module.
"""

from background_process_auditor.core.safety import SafetyGuard

def test_critical_processes_cannot_be_terminated():
    assert SafetyGuard.is_critical_process("system") is True
    assert SafetyGuard.is_critical_process("csrss.exe") is True
    assert SafetyGuard.is_critical_process("lsass") is True
    assert SafetyGuard.is_critical_process("svchost.exe") is True
    assert SafetyGuard.can_terminate("services.exe") is False
    assert SafetyGuard.can_terminate("wininit.exe", pid=4) is False

def test_non_critical_processes_can_be_terminated():
    assert SafetyGuard.is_critical_process("my_custom_app.exe") is False
    assert SafetyGuard.can_terminate("my_custom_app.exe", pid=1234) is True

def test_security_services_protected():
    assert SafetyGuard.is_security_service("WinDefend") is True
    assert SafetyGuard.is_security_service("MpsSvc") is True
    assert SafetyGuard.can_disable_startup("Windows Security", "MSASCuiL.exe") is False
    assert SafetyGuard.can_disable_startup("UserApp", "C:\\Apps\\test.exe") is True
