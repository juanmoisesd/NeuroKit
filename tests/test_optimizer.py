import pytest
from src.optimizer.config_manager import ConfigManager, OptimizerMode
from src.storage.db import DatabaseManager

@pytest.fixture
def config_manager():
    db = DatabaseManager(":memory:")
    cm = ConfigManager(db)
    cm.is_windows = False # Force mock mode
    yield cm
    db.conn.close()

def test_get_recommendations(config_manager):
    current = {
        "TransmitPower": "Medium",
        "PreferredBand": "No Preference",
        "UnknownProperty": "Blah"
    }

    recs = config_manager.get_recommendations("Wi-Fi", current)

    assert len(recs) == 2

    power_rec = next(r for r in recs if r["property"] == "TransmitPower")
    assert power_rec["current"] == "Medium"
    assert power_rec["proposed"] == "Highest"

    band_rec = next(r for r in recs if r["property"] == "PreferredBand")
    assert band_rec["current"] == "No Preference"
    assert band_rec["proposed"] == "Prefer 5GHz band"

def test_apply_optimization_requires_mode(config_manager):
    config_manager.set_mode(OptimizerMode.RECOMMENDATION)
    success, msg = config_manager.apply_optimization("Wi-Fi", "TransmitPower", "Highest", "Medium")
    assert not success
    assert "Optimization mode" in msg

def test_apply_optimization_success(config_manager):
    config_manager.set_mode(OptimizerMode.OPTIMIZATION)
    success, msg = config_manager.apply_optimization("Wi-Fi", "TransmitPower", "Highest", "Medium")

    assert success

    # Check DB was updated
    history = config_manager.db_manager.get_config_history()
    assert len(history) == 1
    assert history[0]["property_name"] == "TransmitPower"

def test_revert_optimization(config_manager):
    config_manager.set_mode(OptimizerMode.OPTIMIZATION)
    # Apply change
    config_manager.apply_optimization("Wi-Fi", "TransmitPower", "Highest", "Medium")

    history = config_manager.db_manager.get_config_history()
    change_id = history[0]["id"]

    success, msg = config_manager.revert_optimization(change_id)
    assert success
