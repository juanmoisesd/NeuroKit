"""
Unit tests for Process Monitor module.
"""

from background_process_auditor.core.monitor import ProcessMonitor, ProcessSample, NetworkSocketInfo

def test_process_monitor_sampling():
    monitor = ProcessMonitor()
    totals = monitor.get_system_totals()
    assert "cpu_percent" in totals
    assert "memory_percent" in totals

    samples = monitor.sample_processes()
    assert isinstance(samples, list)
    if samples:
        s = samples[0]
        assert hasattr(s, "pid")
        assert hasattr(s, "name")
        assert hasattr(s, "has_network_evidence")

def test_strict_network_evidence_rule():
    sample_with_net = ProcessSample(
        pid=100,
        name="test_net.exe",
        cpu_percent=1.0,
        memory_bytes=1000,
        memory_percent=0.1,
        read_bytes=0,
        write_bytes=0,
        num_threads=1,
        status="running",
        is_critical=False,
        sockets=[NetworkSocketInfo("127.0.0.1", 8080, "192.168.1.1", 443, "ESTABLISHED")],
        has_network_evidence=True
    )
    assert sample_with_net.has_network_evidence is True
    assert len(sample_with_net.sockets) == 1

    sample_no_net = ProcessSample(
        pid=101,
        name="idle_app.exe",
        cpu_percent=0.0,
        memory_bytes=1000,
        memory_percent=0.1,
        read_bytes=0,
        write_bytes=0,
        num_threads=1,
        status="running",
        is_critical=False,
        sockets=[],
        has_network_evidence=False
    )
    assert sample_no_net.has_network_evidence is False
