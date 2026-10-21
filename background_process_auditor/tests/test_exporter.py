"""
Unit tests for CSV Exporter module.
"""

import os
import tempfile
import csv
from background_process_auditor.core.exporter import CSVExporter
from background_process_auditor.core.analyzer import AuditFinding

def test_export_findings_to_csv():
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = os.path.join(tmp_dir, "test_findings.csv")
        finding = AuditFinding(
            id="TEST_01",
            pid=1234,
            process_name="test_proc.exe",
            category="Consumo Elevado",
            impact="Alto",
            confidence="Alta",
            timestamp_str="12:00:00",
            duration_seconds=15.5,
            bytes_transferred=1024,
            evidence_details="CPU Spike",
            is_critical=False
        )
        CSVExporter.export_findings_to_csv([finding], csv_path)

        assert os.path.exists(csv_path)
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["PID"] == "1234"
            assert rows[0]["Nombre de Proceso"] == "test_proc.exe"
            assert rows[0]["Impacto"] == "Alto"
