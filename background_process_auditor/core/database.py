"""
Module: Database Manager
SQLite storage for metric history, process snapshots, and audit findings.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """Handles SQLite persistence for audit history."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            data_dir = os.path.join(os.path.expanduser("~"), ".bg_process_auditor")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "auditor_history.db")
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    timestamp_str TEXT,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    net_bytes_sent INTEGER,
                    net_bytes_recv INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS process_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER,
                    pid INTEGER,
                    name TEXT,
                    cpu_percent REAL,
                    memory_bytes INTEGER,
                    memory_percent REAL,
                    read_bytes INTEGER,
                    write_bytes INTEGER,
                    has_network_evidence INTEGER,
                    is_critical INTEGER,
                    FOREIGN KEY(snapshot_id) REFERENCES system_snapshots(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    pid INTEGER,
                    process_name TEXT,
                    category TEXT,
                    impact TEXT,
                    confidence TEXT,
                    timestamp_str TEXT,
                    duration_seconds REAL,
                    bytes_transferred INTEGER,
                    evidence_details TEXT,
                    is_critical INTEGER
                )
            """)
            conn.commit()

    def save_system_snapshot(self, snapshot: dict) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_snapshots (timestamp, timestamp_str, cpu_percent, memory_percent, disk_percent, net_bytes_sent, net_bytes_recv)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.get("timestamp"),
                snapshot.get("timestamp_str", ""),
                snapshot.get("cpu_percent", 0.0),
                snapshot.get("memory_percent", 0.0),
                snapshot.get("disk_percent", 0.0),
                snapshot.get("net_bytes_sent", 0),
                snapshot.get("net_bytes_recv", 0)
            ))
            conn.commit()
            return cursor.lastrowid

    def save_findings(self, findings: List[Any]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for f in findings:
                cursor.execute("""
                    INSERT OR REPLACE INTO findings
                    (id, pid, process_name, category, impact, confidence, timestamp_str, duration_seconds, bytes_transferred, evidence_details, is_critical)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f.id,
                    f.pid,
                    f.process_name,
                    f.category,
                    f.impact,
                    f.confidence,
                    f.timestamp_str,
                    f.duration_seconds,
                    f.bytes_transferred,
                    f.evidence_details,
                    1 if f.is_critical else 0
                ))
            conn.commit()

    def get_recent_system_snapshots(self, limit: int = 60) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_snapshots ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in reversed(rows)]

    def get_all_findings(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM findings ORDER BY timestamp_str DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
