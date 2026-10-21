"""Pruebas unitarias e integración para Safe Debloat Manager."""

import os
import shutil
import tempfile
import pytest

from safe_debloat_manager.core.models import (
    DebloatItem,
    ItemCategory,
    SafetyLevel,
    format_size,
)
from safe_debloat_manager.core.exclusions import (
    evaluate_exclusion,
    is_critical_system_path,
)
from safe_debloat_manager.core.scanner import DebloatScanner
from safe_debloat_manager.core.cleaner import DebloatCleaner
from safe_debloat_manager.core.logger import ActionLogger
from safe_debloat_manager.core.recovery import RecoveryManager


def test_format_size():
    """Prueba el formateo de bytes a cadenas legibles."""
    assert format_size(500) == "500 B"
    assert format_size(2048) == "2.00 KB"
    assert format_size(1048576 * 5) == "5.00 MB"
    assert format_size(1073741824 * 3) == "3.00 GB"


def test_debloat_item_serialization():
    """Prueba la creación y serialización de DebloatItem."""
    item = DebloatItem(
        item_id="appx_test",
        name="TestApp",
        category=ItemCategory.PREINSTALLED_APP,
        path_or_package="Microsoft.TestApp_1.0_x64",
        description="Aplicación de prueba",
        size_bytes=10 * 1024 * 1024,
        dependencies="Ninguna",
        is_excluded_by_default=False,
    )
    d = item.to_dict()
    assert d["item_id"] == "appx_test"
    assert d["formatted_size"] == "10.00 MB"
    assert d["category"] == ItemCategory.PREINSTALLED_APP.value


def test_exclusion_rules():
    """Verifica las reglas de exclusión por defecto."""
    # Componentes del sistema
    is_exc, reason, safety = evaluate_exclusion(
        ItemCategory.PREINSTALLED_APP, "ShellExperienceHost", "Microsoft.Windows.ShellExperienceHost"
    )
    assert is_exc is True
    assert safety == SafetyLevel.EXCLUDED

    # Controladores
    is_exc, reason, safety = evaluate_exclusion(
        ItemCategory.STARTUP_APP, "Realtek Audio Console", "C:\\Program Files\\Realtek\\RtkAudio.exe"
    )
    assert is_exc is True

    # Runtimes compartidos
    is_exc, reason, safety = evaluate_exclusion(
        ItemCategory.PREINSTALLED_APP, "Microsoft Visual C++ Runtime", "Microsoft.VCLibs.140.00"
    )
    assert is_exc is True

    # Herramientas de seguridad
    is_exc, reason, safety = evaluate_exclusion(
        ItemCategory.PREINSTALLED_APP, "Windows Defender Security", "Microsoft.WindowsDefender"
    )
    assert is_exc is True

    # Aplicación bloatware estándar no crítica
    is_exc, reason, safety = evaluate_exclusion(
        ItemCategory.PREINSTALLED_APP, "Candy Crush Saga", "Microsoft.CandyCrushSaga"
    )
    assert is_exc is False
    assert safety == SafetyLevel.SAFE


def test_critical_system_paths():
    """Verifica el bloqueo estricto de rutas críticas del sistema."""
    assert is_critical_system_path("C:\\") is True
    assert is_critical_system_path("C:\\Windows") is True
    assert is_critical_system_path("C:\\Windows\\System32") is True
    assert is_critical_system_path("C:\\Program Files") is True
    assert is_critical_system_path("/tmp/safe_folder") is False


def test_scanner_mock_execution():
    """Prueba el funcionamiento del escáner en modo de prueba."""
    scanner = DebloatScanner(force_mock=True)
    items = scanner.scan_all()

    assert len(items) > 0
    categories = {i.category for i in items}
    assert ItemCategory.PREINSTALLED_APP in categories
    assert ItemCategory.STARTUP_APP in categories
    assert ItemCategory.SAFE_TEMP in categories

    # Verificar que los excluidos por defecto no vienen seleccionados por defecto
    for item in items:
        if item.is_excluded_by_default:
            assert item.is_selected is False


def test_cleaner_simulation_mode():
    """Prueba la ejecución de la limpieza en Modo Simulación."""
    logger = ActionLogger()
    recovery = RecoveryManager(backup_dir=tempfile.mkdtemp())
    cleaner = DebloatCleaner(logger=logger, recovery_mgr=recovery)

    item = DebloatItem(
        item_id="mock_app",
        name="Mock Bloatware",
        category=ItemCategory.PREINSTALLED_APP,
        path_or_package="Mock.Package",
        description="Juego de prueba",
        size_bytes=50 * 1024 * 1024,
        dependencies="Ninguna",
        is_selected=True,
    )

    res = cleaner.execute_cleaning([item], simulation_mode=True, create_restore_point=False)
    assert res.simulation_mode is True
    assert res.successful == 1
    assert res.bytes_freed == 50 * 1024 * 1024

    records = logger.get_all_records()
    assert len(records) == 1
    assert records[0].action_type == "SIMULACION"
    assert records[0].status == "EXITO"


def test_cleaner_safe_temp_removal():
    """Prueba el borrado real y seguro de archivos temporales en una carpeta de pruebas."""
    test_dir = tempfile.mkdtemp(prefix="safe_debloat_test_")
    file1 = os.path.join(test_dir, "temp1.txt")
    file2 = os.path.join(test_dir, "temp2.log")

    with open(file1, "w") as f:
        f.write("A" * 1024)
    with open(file2, "w") as f:
        f.write("B" * 2048)

    item = DebloatItem(
        item_id="temp_test",
        name="Carpeta Temp de Prueba",
        category=ItemCategory.SAFE_TEMP,
        path_or_package=test_dir,
        description="Carpeta temporal",
        size_bytes=3072,
        dependencies="Ninguna",
        is_selected=True,
    )

    cleaner = DebloatCleaner()
    res = cleaner.execute_cleaning([item], simulation_mode=False, create_restore_point=False)

    assert res.successful == 1
    assert res.bytes_freed == 3072
    # La carpeta raíz debe seguir existiendo, pero los archivos deben haberse vaciado
    assert os.path.exists(test_dir)
    assert len(os.listdir(test_dir)) == 0

    shutil.rmtree(test_dir, ignore_errors=True)


def test_blocked_system_path_cleaning():
    """Garantiza que el motor de limpieza bloquee cualquier intento de borrar carpetas del sistema."""
    item = DebloatItem(
        item_id="system_path_test",
        name="Intento de borrado ilegal",
        category=ItemCategory.SAFE_TEMP,
        path_or_package="C:\\Windows\\System32",
        description="Directorio protegido",
        size_bytes=1000000,
        dependencies="Crítico",
        is_selected=True,
    )

    cleaner = DebloatCleaner()
    res = cleaner.execute_cleaning([item], simulation_mode=False, create_restore_point=False)

    assert res.failed == 1
    assert res.successful == 0


def test_recovery_manager_backups():
    """Prueba la creación y lectura de respaldos de registro."""
    tmp_backup_dir = tempfile.mkdtemp()
    mgr = RecoveryManager(backup_dir=tmp_backup_dir)

    backup_path = mgr.backup_startup_item(
        item_name="SpotifyStartup",
        reg_key=r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        reg_value_name="Spotify",
        raw_command="C:\\Users\\Test\\Spotify.exe",
    )

    assert os.path.exists(backup_path)
    backups = mgr.get_all_backups()
    assert len(backups) == 1
    assert backups[0]["item_name"] == "SpotifyStartup"

    shutil.rmtree(tmp_backup_dir, ignore_errors=True)


def test_logger_export():
    """Prueba la exportación del registro de acciones a archivo .log."""
    logger = ActionLogger()
    logger.log_action("id1", "Item1", "Cat1", "SIMULACION", "EXITO", 1024, "Mensaje 1")

    tmp_log = tempfile.mktemp(suffix=".log")
    ok = logger.export_log(tmp_log)
    assert ok is True
    assert os.path.exists(tmp_log)

    with open(tmp_log, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Item1" in content
        assert "SIMULACION" in content

    if os.path.exists(tmp_log):
        os.remove(tmp_log)


def test_gui_app_initialization():
    """Prueba la inicialización y manipulación básica de la interfaz gráfica."""
    import tkinter as tk
    from safe_debloat_manager.gui.app import SafeDebloatApp

    try:
        app = SafeDebloatApp(force_mock=True)
        app.withdraw()  # Ocultar ventana durante el test headless

        assert len(app.items) > 0

        # Probar controles de selección
        app._deselect_all()
        assert sum(1 for i in app.items if i.is_selected) == 0

        app._select_safe_only()
        safe_count = sum(1 for i in app.items if not i.is_excluded_by_default)
        assert sum(1 for i in app.items if i.is_selected) == safe_count

        app._invert_selection()
        assert sum(1 for i in app.items if i.is_selected) == len(app.items) - safe_count

        app.destroy()
    except tk.TclError:
        pytest.skip("Entorno gráfico no disponible para inicializar Tkinter")
