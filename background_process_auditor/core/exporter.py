"""
Module: CSV Exporter
Exports process metrics, audit findings, and historical system stats to CSV format.
"""

import csv
from typing import List, Dict, Any, Union
from background_process_auditor.core.analyzer import AuditFinding

class CSVExporter:
    """Handles generation of CSV reports."""

    @staticmethod
    def export_findings_to_csv(findings: Union[List[AuditFinding], List[Dict[str, Any]]], output_filepath: str) -> None:
        """Exports audit findings to a CSV file."""
        fieldnames = [
            "ID",
            "PID",
            "Nombre de Proceso",
            "Categoría",
            "Impacto",
            "Confianza",
            "Hora / Fecha",
            "Duración (s)",
            "Bytes Transferidos",
            "Detalles y Evidencia",
            "Es Crítico"
        ]

        with open(output_filepath, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in findings:
                if isinstance(item, AuditFinding):
                    row = {
                        "ID": item.id,
                        "PID": item.pid,
                        "Nombre de Proceso": item.process_name,
                        "Categoría": item.category,
                        "Impacto": item.impact,
                        "Confianza": item.confidence,
                        "Hora / Fecha": item.timestamp_str,
                        "Duración (s)": round(item.duration_seconds, 2),
                        "Bytes Transferidos": item.bytes_transferred,
                        "Detalles y Evidencia": item.evidence_details,
                        "Es Crítico": "Sí" if item.is_critical else "No"
                    }
                else:
                    row = {
                        "ID": item.get("id", ""),
                        "PID": item.get("pid", 0),
                        "Nombre de Proceso": item.get("process_name", ""),
                        "Categoría": item.get("category", ""),
                        "Impacto": item.get("impact", ""),
                        "Confianza": item.get("confidence", ""),
                        "Hora / Fecha": item.get("timestamp_str", ""),
                        "Duración (s)": round(item.get("duration_seconds", 0), 2),
                        "Bytes Transferidos": item.get("bytes_transferred", 0),
                        "Detalles y Evidencia": item.get("evidence_details", ""),
                        "Es Crítico": "Sí" if item.get("is_critical") else "No"
                    }
                writer.writerow(row)

    @staticmethod
    def export_process_samples_to_csv(samples: List[Any], output_filepath: str) -> None:
        """Exports process samples to a CSV file."""
        fieldnames = [
            "PID",
            "Nombre",
            "CPU (%)",
            "RAM (MB)",
            "RAM (%)",
            "Lectura Disco (Bytes)",
            "Escritura Disco (Bytes)",
            "Evidencia de Red",
            "Sockets Activos",
            "Es Crítico"
        ]

        with open(output_filepath, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for s in samples:
                row = {
                    "PID": s.pid,
                    "Nombre": s.name,
                    "CPU (%)": f"{s.cpu_percent:.1f}",
                    "RAM (MB)": f"{s.memory_bytes / (1024 * 1024):.1f}",
                    "RAM (%)": f"{s.memory_percent:.1f}",
                    "Lectura Disco (Bytes)": s.read_bytes,
                    "Escritura Disco (Bytes)": s.write_bytes,
                    "Evidencia de Red": "Confirmada" if s.has_network_evidence else "Sin Evidencia Directa",
                    "Sockets Activos": len(s.sockets),
                    "Es Crítico": "Sí" if s.is_critical else "No"
                }
                writer.writerow(row)
