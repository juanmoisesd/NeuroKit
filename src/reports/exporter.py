import csv
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ReportExporter:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def export_to_csv(self, filename):
        """Export metrics to a CSV file."""
        try:
            metrics = self.db_manager.get_metrics(limit=10000) # Get all reasonable data
            if not metrics:
                logger.warning("No metrics to export.")
                return False, "No data available."

            fieldnames = ["id", "timestamp", "latency_median", "packet_loss", "jitter", "ssid", "signal"]

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

            with open(filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in metrics:
                    writer.writerow(row)

            return True, f"Exported successfully to {filename}"
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False, str(e)

    def export_to_json(self, filename):
        """Export metrics and events to a JSON file."""
        try:
            metrics = self.db_manager.get_metrics(limit=10000)

            # Get events too
            events = []
            try:
                import sqlite3
                self.db_manager.conn.row_factory = sqlite3.Row
                cursor = self.db_manager.conn.cursor()
                cursor.execute("SELECT * FROM events")
                events = [dict(row) for row in cursor.fetchall()]
            except Exception:
                pass

            data = {
                 "export_time": datetime.now().isoformat(),
                 "metrics": metrics,
                 "events": events
            }

            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

            with open(filename, mode='w', encoding='utf-8') as f:
                 json.dump(data, f, indent=4)

            return True, f"Exported successfully to {filename}"
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False, str(e)
