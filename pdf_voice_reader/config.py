import json
import os
from typing import Dict, Any

class ConfigManager:
    """Manages application settings and state using a JSON file."""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.default_config = {
            "recent_files": [],
            "last_positions": {}, # Mapping of filepath to last paragraph index
            "voice_id": None,
            "rate": 150,
            "ocr_language": "spa"
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Loads configuration from JSON file or creates defaults."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Fallback to default if file is corrupted
                return self.default_config.copy()
        else:
            return self.default_config.copy()

    def save_config(self):
        """Saves current configuration to JSON file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error guardando configuración: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Gets a configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Sets a configuration value and saves."""
        self.config[key] = value
        self.save_config()

    def add_recent_file(self, filepath: str):
        """Adds a file to the recent files list."""
        recent_files = self.config.get("recent_files", [])
        if filepath in recent_files:
            recent_files.remove(filepath)
        recent_files.insert(0, filepath)

        # Keep only the last 10 recent files
        self.config["recent_files"] = recent_files[:10]
        self.save_config()

    def get_recent_files(self) -> list:
        return self.config.get("recent_files", [])

    def save_last_position(self, filepath: str, page_index: int, block_index: int):
        """Saves the last reading position for a specific file."""
        positions = self.config.get("last_positions", {})
        positions[filepath] = {"page": page_index, "block": block_index}
        self.config["last_positions"] = positions
        self.save_config()

    def get_last_position(self, filepath: str) -> tuple:
        """Retrieves the last reading position for a specific file."""
        positions = self.config.get("last_positions", {})
        pos = positions.get(filepath, {"page": 0, "block": 0})
        return pos.get("page", 0), pos.get("block", 0)
