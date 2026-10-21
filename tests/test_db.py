import pytest
import os
import sqlite3
import json
from src.storage.db import DatabaseManager

@pytest.fixture
def db_manager():
    # Use an in-memory database for testing
    db = DatabaseManager(":memory:")
    yield db

def test_insert_and_get_metrics(db_manager):
    db_manager.insert_metric(15.5, 0.0, 2.1, "MyWiFi", "85%")
    db_manager.insert_metric(20.1, 5.0, 4.0, "MyWiFi", "80%")

    metrics = db_manager.get_metrics()
    assert len(metrics) == 2
    assert metrics[0]["latency_median"] == 20.1  # Most recent first
    assert metrics[1]["latency_median"] == 15.5
    assert metrics[0]["packet_loss"] == 5.0
    assert metrics[1]["ssid"] == "MyWiFi"

def test_config_history(db_manager):
    db_manager.record_config_change("Wi-Fi", "RoamingAggressiveness", "Medium", "High")

    history = db_manager.get_config_history()
    assert len(history) == 1
    assert history[0]["adapter_name"] == "Wi-Fi"
    assert history[0]["property_name"] == "RoamingAggressiveness"
    assert history[0]["old_value"] == "Medium"
    assert history[0]["new_value"] == "High"
    assert history[0]["status"] == "applied"

def test_log_event(db_manager):
    db_manager.log_event("DISCONNECT", "Wi-Fi adapter disconnected", {"reason": "User action"})

    # Retrieve using the same connection since memory db goes away otherwise
    db_manager.conn.row_factory = sqlite3.Row
    cursor = db_manager.conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = [dict(row) for row in cursor.fetchall()]

    assert len(events) == 1
    assert events[0]["event_type"] == "DISCONNECT"
    details = json.loads(events[0]["details"])
    assert details["reason"] == "User action"
