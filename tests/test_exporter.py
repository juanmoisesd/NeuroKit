import pytest
import os
import json
import csv
from src.reports.exporter import ReportExporter
from src.storage.db import DatabaseManager

@pytest.fixture
def exporter(tmp_path):
    db = DatabaseManager(":memory:")
    # Add some dummy data
    db.insert_metric(20.5, 0.0, 2.0, "TestNet", "85%")
    db.log_event("TEST", "Test event", {"info": "test"})

    exp = ReportExporter(db)
    yield exp, tmp_path
    db.conn.close()

def test_export_csv(exporter):
    exp, tmp_path = exporter
    csv_file = tmp_path / "export.csv"

    success, msg = exp.export_to_csv(str(csv_file))

    assert success
    assert csv_file.exists()

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["ssid"] == "TestNet"
        assert rows[0]["latency_median"] == "20.5"

def test_export_json(exporter):
    exp, tmp_path = exporter
    json_file = tmp_path / "export.json"

    success, msg = exp.export_to_json(str(json_file))

    assert success
    assert json_file.exists()

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert "metrics" in data
    assert "events" in data
    assert len(data["metrics"]) == 1
    assert data["metrics"][0]["ssid"] == "TestNet"
    assert len(data["events"]) == 1
    assert data["events"][0]["event_type"] == "TEST"
