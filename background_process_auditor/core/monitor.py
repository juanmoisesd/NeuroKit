"""
Module: Process & Network Monitor
Samples system processes (CPU, RAM, Disk I/O) and active network sockets.
Strictly attributes network activity to PIDs only when direct socket evidence exists.
"""

import time

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import psutil

from background_process_auditor.core.safety import SafetyGuard

@dataclass
class NetworkSocketInfo:
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    status: str

@dataclass
class ProcessSample:
    pid: int
    name: str
    cpu_percent: float
    memory_bytes: int
    memory_percent: float
    read_bytes: int
    write_bytes: int
    num_threads: int
    status: str
    is_critical: bool
    sockets: List[NetworkSocketInfo] = field(default_factory=list)
    has_network_evidence: bool = False
    net_bytes_sent: int = 0
    net_bytes_recv: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

class ProcessMonitor:
    """Monitors system processes and performs strict evidence-based network attribution."""

    def __init__(self) -> None:
        self.process_history: Dict[int, ProcessSample] = {}
        # Stores previous per-process I/O counters for delta measurements
        self._prev_io: Dict[int, tuple] = {}
        self._last_sample_time: float = time.time()

    def get_system_totals(self) -> dict:
        """Returns overall system resource usage."""
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/") if hasattr(psutil, "disk_usage") else None
        net_io = psutil.net_io_counters()

        return {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_bytes": mem.used,
            "memory_total_bytes": mem.total,
            "disk_percent": disk.percent if disk else 0.0,
            "net_bytes_sent": net_io.bytes_sent if net_io else 0,
            "net_bytes_recv": net_io.bytes_recv if net_io else 0,
            "timestamp": time.time(),
        }

    def sample_processes(self) -> List[ProcessSample]:
        """
        Samples all accessible processes and maps active socket connections per PID.
        Enforces Strict Evidence Rule: Never attributes traffic to a PID without open socket endpoints.
        """
        now = time.time()
        pid_sockets: Dict[int, List[NetworkSocketInfo]] = {}

        # Collect active connections using psutil
        try:
            connections = psutil.net_connections(kind="inet")
            for conn in connections:
                if conn.pid and conn.pid > 0:
                    sock_info = NetworkSocketInfo(
                        local_address=conn.laddr.ip if conn.laddr else "",
                        local_port=conn.laddr.port if conn.laddr else 0,
                        remote_address=conn.raddr.ip if conn.raddr else "",
                        remote_port=conn.raddr.port if conn.raddr else 0,
                        status=conn.status,
                    )
                    pid_sockets.setdefault(conn.pid, []).append(sock_info)
        except Exception:
            # Fallback if permission issues prevent global net_connections
            pass

        samples: List[ProcessSample] = []

        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'memory_percent', 'num_threads', 'status', 'io_counters']):
            try:
                info = p.info
                pid = info['pid']
                name = info['name'] or f"PID_{pid}"

                mem_info = info.get('memory_info')
                mem_bytes = mem_info.rss if mem_info else 0
                mem_pct = info.get('memory_percent') or 0.0

                io = info.get('io_counters')
                read_bytes = io.read_bytes if io else 0
                write_bytes = io.write_bytes if io else 0

                cpu_pct = info.get('cpu_percent') or 0.0
                threads = info.get('num_threads') or 1
                status = info.get('status') or "running"

                # Check socket evidence for PID
                sockets = pid_sockets.get(pid, [])
                if not sockets:
                    # Try per-process connections fallback if net_connections had permission limits
                    try:
                        p_conns = p.net_connections(kind="inet")
                        for conn in p_conns:
                            sockets.append(NetworkSocketInfo(
                                local_address=conn.laddr.ip if conn.laddr else "",
                                local_port=conn.laddr.port if conn.laddr else 0,
                                remote_address=conn.raddr.ip if conn.raddr else "",
                                remote_port=conn.raddr.port if conn.raddr else 0,
                                status=conn.status,
                            ))
                    except Exception:
                        pass

                has_evidence = len(sockets) > 0
                is_crit = SafetyGuard.is_critical_process(name, pid) or SafetyGuard.is_security_service(name)

                prev_sample = self.process_history.get(pid)
                first_seen = prev_sample.first_seen if prev_sample else now

                sample = ProcessSample(
                    pid=pid,
                    name=name,
                    cpu_percent=cpu_pct,
                    memory_bytes=mem_bytes,
                    memory_percent=mem_pct,
                    read_bytes=read_bytes,
                    write_bytes=write_bytes,
                    num_threads=threads,
                    status=status,
                    is_critical=is_crit,
                    sockets=sockets,
                    has_network_evidence=has_evidence,
                    first_seen=first_seen,
                    last_seen=now,
                )

                self.process_history[pid] = sample
                samples.append(sample)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        self._last_sample_time = now
        return samples
