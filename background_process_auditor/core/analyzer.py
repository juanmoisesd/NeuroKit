"""
Module: Process Findings Analyzer
Analyzes process metrics to identify background activity patterns:
- Actividad Persistente (persistent background running)
- Consumo Elevado (high CPU/RAM consumption)
- Conexiones Frecuentes (frequent network activity)
Categorizes findings by Impacto (Alto, Medio, Bajo) and Confianza (Alta, Media, Baja).
"""

import time
from dataclasses import dataclass
from typing import List

from background_process_auditor.core.monitor import ProcessSample


@dataclass
class AuditFinding:
    id: str
    pid: int
    process_name: str
    category: str  # "Actividad Persistente", "Consumo Elevado", "Conexiones Frecuentes"
    impact: str    # "Alto", "Medio", "Bajo"
    confidence: str # "Alta", "Media", "Baja"
    timestamp_str: str
    duration_seconds: float
    bytes_transferred: int
    evidence_details: str
    is_critical: bool


class ProcessAnalyzer:
    """Evaluates process metric streams and isolates background anomalies."""

    def __init__(self) -> None:
        pass

    def analyze_samples(self, samples: List[ProcessSample]) -> List[AuditFinding]:
        findings: List[AuditFinding] = []
        now_str = time.strftime("%H:%M:%S - %d/%m/%Y")

        for s in samples:
            duration = max(1.0, s.last_seen - s.first_seen)

            # 1. Evaluate "Consumo Elevado"
            if s.cpu_percent >= 30.0 or s.memory_bytes >= (500 * 1024 * 1024):
                if s.cpu_percent >= 70.0 or s.memory_bytes >= (1024 * 1024 * 1024):
                    impact = "Alto"
                else:
                    impact = "Medio"

                confidence = "Alta"
                finding_id = f"HIGH_RES_{s.pid}_{int(s.first_seen)}"
                evidence = f"Uso de CPU: {s.cpu_percent:.1f}%, RAM: {s.memory_bytes / (1024*1024):.1f} MB"
                findings.append(
                    AuditFinding(
                        id=finding_id,
                        pid=s.pid,
                        process_name=s.name,
                        category="Consumo Elevado",
                        impact=impact,
                        confidence=confidence,
                        timestamp_str=now_str,
                        duration_seconds=duration,
                        bytes_transferred=s.read_bytes + s.write_bytes,
                        evidence_details=evidence,
                        is_critical=s.is_critical,
                    )
                )

            # 2. Evaluate "Conexiones Frecuentes"
            if s.has_network_evidence and len(s.sockets) > 0:
                conn_count = len(s.sockets)
                if conn_count >= 5:
                    impact = "Alto"
                elif conn_count >= 2:
                    impact = "Medio"
                else:
                    impact = "Bajo"

                # Direct socket endpoints mean Alta confidence
                confidence = "Alta"
                endpoints = ", ".join([f"{sock.remote_address}:{sock.remote_port}" for sock in s.sockets[:3]])
                finding_id = f"NET_FREQ_{s.pid}_{int(s.first_seen)}"
                evidence = f"{conn_count} conexiones activas confirmadas por sockets. Conexiones: {endpoints}"
                findings.append(
                    AuditFinding(
                        id=finding_id,
                        pid=s.pid,
                        process_name=s.name,
                        category="Conexiones Frecuentes",
                        impact=impact,
                        confidence=confidence,
                        timestamp_str=now_str,
                        duration_seconds=duration,
                        bytes_transferred=s.net_bytes_sent + s.net_bytes_recv,
                        evidence_details=evidence,
                        is_critical=s.is_critical,
                    )
                )

            # 3. Evaluate "Actividad Persistente"
            # Processes running in background continuously without active user focus
            if duration >= 10.0 and not s.is_critical and (s.cpu_percent > 1.0 or s.memory_bytes > (100 * 1024 * 1024)):
                impact = "Medio" if s.memory_bytes > (300 * 1024 * 1024) else "Bajo"
                confidence = "Alta" if s.has_network_evidence else "Media"
                finding_id = f"PERSIST_{s.pid}_{int(s.first_seen)}"
                evidence = f"Ejecución continua en segundo plano durante {duration:.0f}s sin interactividad activa de pantalla."
                findings.append(
                    AuditFinding(
                        id=finding_id,
                        pid=s.pid,
                        process_name=s.name,
                        category="Actividad Persistente",
                        impact=impact,
                        confidence=confidence,
                        timestamp_str=now_str,
                        duration_seconds=duration,
                        bytes_transferred=s.read_bytes + s.write_bytes + s.net_bytes_sent + s.net_bytes_recv,
                        evidence_details=evidence,
                        is_critical=s.is_critical,
                    )
                )

        return findings
