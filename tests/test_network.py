import pytest
from src.network.adapter import NetworkAdapter
from src.network.connectivity import ConnectivityChecker

def test_get_interfaces():
    adapter = NetworkAdapter()
    adapter.is_windows = True # Force true for test

    # Mock _run_command to return typical netsh output
    def mock_run_command(cmd):
        if cmd == ["netsh", "wlan", "show", "interfaces"]:
            return """
There is 1 interface on the system:

    Name                   : Wi-Fi
    Description            : Intel(R) Wi-Fi 6 AX201 160MHz
    GUID                   : 12345678-1234-1234-1234-123456789abc
    Physical address       : aa:bb:cc:dd:ee:ff
    State                  : connected
    SSID                   : MyNetwork
    BSSID                  : 11:22:33:44:55:66
    Network type           : Infrastructure
    Radio type             : 802.11ac
    Authentication         : WPA2-Personal
    Cipher                 : CCMP
    Connection mode        : Profile
    Channel                : 36
    Receive rate (Mbps)    : 866.7
    Transmit rate (Mbps)   : 866.7
    Signal                 : 85%
    Profile                : MyNetwork
"""
        return ""

    adapter._run_command = mock_run_command

    interfaces = adapter.get_interfaces()
    assert len(interfaces) == 1
    assert interfaces[0]["name"] == "Wi-Fi"
    assert interfaces[0]["ssid"] == "MyNetwork"
    assert interfaces[0]["signal"] == "85%"
    assert interfaces[0]["channel"] == "36"

def test_connectivity_checker():
    checker = ConnectivityChecker()
    checker.is_windows = True

    # Mock _run_ping
    def mock_run_ping(host, count=1, timeout=2):
        if host == "192.168.1.1":
            return 2.5
        elif host == "8.8.8.8":
            return 15.0
        return None

    checker._run_ping = mock_run_ping

    success, latency = checker.check_local_gateway("192.168.1.1")
    assert success is True
    assert latency == 2.5

    success, latency = checker.check_internet_access()
    assert success is True
    assert latency == 15.0

    success, latency = checker.check_local_gateway(None)
    assert success is False
