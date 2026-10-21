import sqlite3
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="wifi_performance.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database with required tables."""
        try:
            cursor = self.conn.cursor()

            # Metrics history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    latency_median REAL,
                    packet_loss REAL,
                    jitter REAL,
                    ssid TEXT,
                    signal TEXT
                )
            ''')

            # Configuration changes table (for reversions)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    adapter_name TEXT,
                    property_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    status TEXT
                )
            ''')

            # Events table (disconnections, degraded performance)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT,
                    description TEXT,
                    details TEXT
                )
            ''')

            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")

    def insert_metric(self, latency_median, packet_loss, jitter, ssid, signal):
        """Insert a new metrics record."""
        try:
            cursor = self.conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO metrics (timestamp, latency_median, packet_loss, jitter, ssid, signal)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, latency_median, packet_loss, jitter, ssid, signal))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error inserting metric: {e}")
            return None

    def get_metrics(self, limit=100):
        """Retrieve recent metrics."""
        try:
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM metrics ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching metrics: {e}")
            return []

    def record_config_change(self, adapter_name, property_name, old_value, new_value):
        """Record a configuration change for potential reversion."""
        try:
            cursor = self.conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO config_changes (timestamp, adapter_name, property_name, old_value, new_value, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, adapter_name, property_name, str(old_value), str(new_value), "applied"))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error recording config change: {e}")
            return None

    def get_config_history(self):
        """Get history of configuration changes."""
        try:
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM config_changes ORDER BY timestamp DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching config history: {e}")
            return []

    def log_event(self, event_type, description, details=None):
        """Log system events like disconnections or diagnostics."""
        try:
            cursor = self.conn.cursor()
            timestamp = datetime.now().isoformat()
            details_json = json.dumps(details) if details else None
            cursor.execute('''
                INSERT INTO events (timestamp, event_type, description, details)
                VALUES (?, ?, ?, ?)
            ''', (timestamp, event_type, description, details_json))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error logging event: {e}")
            return None

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()
