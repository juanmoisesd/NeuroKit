import pytest
from src.wifi.scanner import WiFiScanner

def test_parse_networks():
    scanner = WiFiScanner()
    scanner.is_windows = True

    sample_output = """
Interface name : Wi-Fi
There are 2 networks currently visible.

SSID 1 : HomeNetwork
    Network type            : Infrastructure
    Authentication          : WPA2-Personal
    Encryption              : CCMP
    BSSID 1                 : 00:11:22:33:44:55
         Signal             : 80%
         Radio type         : 802.11ac
         Channel            : 36
    BSSID 2                 : 00:11:22:33:44:66
         Signal             : 45%
         Radio type         : 802.11n
         Channel            : 6

SSID 2 : GuestNetwork
    Network type            : Infrastructure
    Authentication          : Open
    Encryption              : None
    BSSID 1                 : aa:bb:cc:dd:ee:ff
         Signal             : 90%
         Radio type         : 802.11ax
         Channel            : 149
"""

    networks = scanner._parse_networks(sample_output)

    assert len(networks) == 3

    assert networks[0]["ssid"] == "HomeNetwork"
    assert networks[0]["security"] == "WPA2-Personal"
    assert networks[0]["bssid"] == "00:11:22:33:44:55"
    assert networks[0]["signal"] == "80%"
    assert networks[0]["channel"] == "36"
    assert networks[0]["band"] == "5 GHz"

    assert networks[1]["ssid"] == "HomeNetwork"
    assert networks[1]["bssid"] == "00:11:22:33:44:66"
    assert networks[1]["signal"] == "45%"
    assert networks[1]["channel"] == "6"
    assert networks[1]["band"] == "2.4 GHz"

    assert networks[2]["ssid"] == "GuestNetwork"
    assert networks[2]["security"] == "Open"
    assert networks[2]["bssid"] == "aa:bb:cc:dd:ee:ff"
    assert networks[2]["channel"] == "149"
    assert networks[2]["band"] == "5 GHz"

def test_analyze_networks():
    scanner = WiFiScanner()
    networks = [
         {"ssid": "Net1", "bssid": "B1", "signal": "40%"},
         {"ssid": "Net2", "bssid": "B2", "signal": "80%"}
    ]

    recommendations = scanner.analyze_networks(networks)

    assert len(recommendations) == 1
    assert recommendations[0]["ssid"] == "Net1"
    assert recommendations[0]["issue"] == "Weak signal"
