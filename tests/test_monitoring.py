import pytest
import sqlite3
from src.monitoring.engine import MonitoringEngine
from src.storage.db import DatabaseManager

class MockAdapter:
    def get_interfaces(self):
        return [{"name": "Wi-Fi", "ssid": "TestNet", "signal": "80%"}]
    def get_ip_config(self, name):
        return {"gateway": "192.168.1.1"}

class MockChecker:
    def check_local_gateway(self, gateway):
        return True, 5.0
    def check_dns_resolution(self):
        return True, 20.0
    def check_internet_access(self):
        return True, 25.0
    def get_quality_metrics(self):
        return {"latency_median": 30.0, "packet_loss": 0.0, "jitter": 2.0}

@pytest.fixture
def monitoring_engine():
    db = DatabaseManager(":memory:")
    engine = MonitoringEngine(db, interval=0.1)
    engine.adapter = MockAdapter()
    engine.checker = MockChecker()
    yield engine
    db.conn.close()

def test_run_checks_records_metrics(monitoring_engine):
    # Run one iteration of checks manually
    monitoring_engine._run_checks()

    metrics = monitoring_engine.db_manager.get_metrics()
    assert len(metrics) == 1
    assert metrics[0]["ssid"] == "TestNet"
    assert metrics[0]["latency_median"] == 30.0
    assert metrics[0]["packet_loss"] == 0.0

def test_analyze_status_logs_events(monitoring_engine):
    # Force a gateway failure
    monitoring_engine.checker.check_local_gateway = lambda gw: (False, None)
    monitoring_engine._run_checks()

    monitoring_engine.db_manager.conn.row_factory = sqlite3.Row
    cursor = monitoring_engine.db_manager.conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = [dict(row) for row in cursor.fetchall()]

    assert len(events) >= 1
    assert any(e["event_type"] == "DEGRADED" and "Cannot reach local gateway" in e["description"] for e in events)

def test_quality_degradation_logs(monitoring_engine):
    # Force high packet loss
    monitoring_engine.checker.get_quality_metrics = lambda: {"latency_median": 40.0, "packet_loss": 25.0, "jitter": 5.0}
    monitoring_engine._run_checks()

    monitoring_engine.db_manager.conn.row_factory = sqlite3.Row
    cursor = monitoring_engine.db_manager.conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = [dict(row) for row in cursor.fetchall()]

    assert any(e["event_type"] == "QUALITY_DROP" and "High packet loss" in e["description"] for e in events)
