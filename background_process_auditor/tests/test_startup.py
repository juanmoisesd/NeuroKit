"""
Unit tests for Startup Manager module.
"""

import os
import tempfile
from background_process_auditor.core.startup import StartupManager

def test_startup_manager_scan_and_backup():
    with tempfile.TemporaryDirectory() as tmp_dir:
        mgr = StartupManager(backup_dir=tmp_dir)
        items = mgr.scan_startup_items()
        assert len(items) > 0

        # Find non-essential item
        non_essential = next((item for item in items if not item.is_essential), None)
        assert non_essential is not None

        # Toggle item
        success, msg = mgr.toggle_item(non_essential.id, False)
        assert success is True
        assert non_essential.enabled is False

        # Verify backup was created
        backups = mgr.list_backups()
        assert len(backups) == 1

        # Restore backup
        restore_ok = mgr.restore_backup(backups[0])
        assert restore_ok is True
        assert mgr.items[non_essential.id].enabled is True

def test_startup_manager_prevents_disabling_essential():
    with tempfile.TemporaryDirectory() as tmp_dir:
        mgr = StartupManager(backup_dir=tmp_dir)
        items = mgr.scan_startup_items()
        essential = next((item for item in items if item.is_essential), None)
        assert essential is not None

        success, msg = mgr.toggle_item(essential.id, False)
        assert success is False
        assert "Acción denegada" in msg
