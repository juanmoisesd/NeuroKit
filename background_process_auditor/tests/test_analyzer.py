"""
Unit tests for Findings Analyzer module.
"""

import time
from background_process_auditor.core.analyzer import ProcessAnalyzer
from background_process_auditor.core.monitor import ProcessSample, NetworkSocketInfo

def test_analyzer_high_resource():
    analyzer = ProcessAnalyzer()
    now = time.time()
    high_cpu_sample = ProcessSample(
        pid=999,
        name="cpu_hog.exe",
        cpu_percent=85.0,
        memory_bytes=2 * 1024 * 1024 * 1024,
        memory_percent=25.0,
        read_bytes=0,
        write_bytes=0,
        num_threads=4,
        status="running",
        is_critical=False,
        sockets=[],
        has_network_evidence=False,
        first_seen=now - 5,
        last_seen=now
    )

    findings = analyzer.analyze_samples([high_cpu_sample])
    assert len(findings) >= 1
    high_res_finding = next(f for f in findings if f.category == "Consumo Elevado")
    assert high_res_finding.impact == "Alto"
    assert high_res_finding.confidence == "Alta"

def test_analyzer_network_frequency():
    analyzer = ProcessAnalyzer()
    now = time.time()
    net_sockets = [
        NetworkSocketInfo("127.0.0.1", 1000 + i, "1.1.1.1", 443, "ESTABLISHED")
        for i in range(6)
    ]
    net_sample = ProcessSample(
        pid=888,
        name="net_app.exe",
        cpu_percent=5.0,
        memory_bytes=50 * 1024 * 1024,
        memory_percent=1.0,
        read_bytes=0,
        write_bytes=0,
        num_threads=2,
        status="running",
        is_critical=False,
        sockets=net_sockets,
        has_network_evidence=True,
        net_bytes_sent=5000,
        net_bytes_recv=15000,
        first_seen=now - 20,
        last_seen=now
    )

    findings = analyzer.analyze_samples([net_sample])
    net_finding = next(f for f in findings if f.category == "Conexiones Frecuentes")
    assert net_finding.impact == "Alto"
    assert net_finding.confidence == "Alta"
    assert net_finding.bytes_transferred == 20000
