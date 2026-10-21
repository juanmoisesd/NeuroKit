import subprocess
import re
import platform
import logging

logger = logging.getLogger(__name__)

class WiFiScanner:
    def __init__(self):
        self.is_windows = platform.system().lower() == "windows"

    def scan_networks(self):
        """Scan for available Wi-Fi networks using netsh."""
        if not self.is_windows:
            logger.debug("Not running on Windows. Mocking network scan.")
            return [
                 {"ssid": "MockNetwork_5G", "bssid": "aa:bb:cc:dd:ee:01", "signal": "90%", "channel": "36", "band": "5 GHz", "security": "WPA2-Personal"},
                 {"ssid": "MockNetwork_2G", "bssid": "aa:bb:cc:dd:ee:02", "signal": "60%", "channel": "6", "band": "2.4 GHz", "security": "WPA2-Personal"}
            ]

        # Use mode=bssid to get detailed info including BSSID, channel, and signal
        cmd = ["netsh", "wlan", "show", "networks", "mode=bssid"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0
            )

            if result.returncode != 0:
                logger.error(f"Error scanning networks: {result.stderr}")
                return []

            return self._parse_networks(result.stdout)

        except Exception as e:
            logger.error(f"Exception during Wi-Fi scan: {e}")
            return []

    def _parse_networks(self, output):
        networks = []
        current_network = {}
        current_bssid = {}

        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("SSID"):
                 # Before starting a new SSID, save the previous one if it has BSSIDs
                 if current_bssid and current_network:
                     net_copy = current_network.copy()
                     net_copy.update(current_bssid)
                     networks.append(net_copy)
                     current_bssid = {}

                 match = re.search(r"SSID \d+ : (.*)", line)
                 if match:
                      # New network group
                      current_network = {"ssid": match.group(1).strip()}
                 else:
                      current_network = {}
            elif line.startswith("Authentication"):
                 match = re.search(r":\s+(.*)", line)
                 if match and current_network:
                      current_network["security"] = match.group(1).strip()
            elif line.startswith("BSSID"):
                 # Save previous BSSID if exists for this SSID
                 if current_bssid and current_network:
                     net_copy = current_network.copy()
                     net_copy.update(current_bssid)
                     networks.append(net_copy)

                 match = re.search(r":\s+(.*)", line)
                 if match:
                      current_bssid = {"bssid": match.group(1).strip()}
            elif line.startswith("Signal"):
                 match = re.search(r":\s+(.*)", line)
                 if match and current_bssid:
                      current_bssid["signal"] = match.group(1).strip()
            elif line.startswith("Radio type"):
                 match = re.search(r":\s+(.*)", line)
                 if match and current_bssid:
                      current_bssid["radio_type"] = match.group(1).strip()
            elif line.startswith("Channel"):
                 match = re.search(r":\s+(.*)", line)
                 if match and current_bssid:
                      channel = match.group(1).strip()
                      current_bssid["channel"] = channel
                      current_bssid["band"] = self._determine_band(channel)
            elif line.startswith("Band"):
                 # Some versions might report Band directly
                 match = re.search(r":\s+(.*)", line)
                 if match and current_bssid:
                      current_bssid["band"] = match.group(1).strip()

        # Add the last one
        if current_bssid and current_network:
             net_copy = current_network.copy()
             net_copy.update(current_bssid)
             networks.append(net_copy)

        return networks

    def _determine_band(self, channel_str):
        try:
            ch = int(channel_str)
            if 1 <= ch <= 14:
                return "2.4 GHz"
            elif 36 <= ch <= 165:
                return "5 GHz"
            elif ch > 165:
                 # Very simplified, 6GHz channels in some regions
                 return "6 GHz"
        except ValueError:
            pass
        return "Unknown"

    def analyze_networks(self, networks):
        """Provide recommendations based on scanned networks."""
        recommendations = []

        # Simple analysis
        for net in networks:
             signal_str = net.get("signal", "0").replace("%", "")
             try:
                 signal = int(signal_str)
                 if signal < 50:
                     recommendations.append({
                          "ssid": net.get("ssid"),
                          "bssid": net.get("bssid"),
                          "issue": "Weak signal",
                          "recommendation": "Consider moving closer to the router or using a repeater."
                     })
             except ValueError:
                 pass

             # Check channel congestion (mock logic)
             # In a real app, we'd group by channel and count SSIDs

        return recommendations
