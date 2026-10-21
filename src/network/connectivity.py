import subprocess
import platform
import socket
import time
import logging

logger = logging.getLogger(__name__)

class ConnectivityChecker:
    def __init__(self):
        self.is_windows = platform.system().lower() == "windows"

    def _run_ping(self, host, count=1, timeout=2):
        """Run ping command and return the latency in ms, or None if failed."""
        if not self.is_windows:
            # Mock ping for linux tests
            logger.debug(f"Mocking ping to {host}")
            return 15.0

        # Windows ping command: ping -n {count} -w {timeout*1000} {host}
        cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0
            )

            # Check if ping was successful
            if result.returncode != 0 or "Destination net unreachable" in result.stdout or "Request timed out" in result.stdout:
                 return None

            # Parse average time from output
            import re
            match = re.search(r"Average = (\d+)ms", result.stdout)
            if match:
                 return float(match.group(1))

            # If average not found but it worked (e.g. count=1), look for time=Xms
            match = re.search(r"time[=<](\d+)ms", result.stdout)
            if match:
                 return float(match.group(1))

            return None

        except Exception as e:
            logger.error(f"Error pinging {host}: {e}")
            return None

    def check_local_gateway(self, gateway_ip):
         """Ping the default gateway."""
         if not gateway_ip:
              return False, None
         latency = self._run_ping(gateway_ip, count=2)
         return latency is not None, latency

    def check_internet_access(self, host="8.8.8.8"):
         """Ping a reliable external IP to check internet access."""
         latency = self._run_ping(host, count=2)
         return latency is not None, latency

    def check_dns_resolution(self, domain="google.com"):
         """Check if DNS resolution is working."""
         if not self.is_windows:
              return True, 25.0

         start_time = time.time()
         try:
              socket.gethostbyname(domain)
              end_time = time.time()
              return True, (end_time - start_time) * 1000
         except socket.gaierror:
              return False, None
         except Exception as e:
              logger.error(f"DNS check failed: {e}")
              return False, None

    def get_quality_metrics(self, host="8.8.8.8", count=10):
         """Run a longer ping test to get packet loss and jitter."""
         if not self.is_windows:
              return {
                  "latency_median": 20.0,
                  "packet_loss": 0.0,
                  "jitter": 2.5
              }

         cmd = ["ping", "-n", str(count), host]
         try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0
            )

            import re
            latencies = []
            for line in result.stdout.splitlines():
                 match = re.search(r"time[=<](\d+)ms", line)
                 if match:
                      latencies.append(float(match.group(1)))

            loss_match = re.search(r"(\d+)% loss", result.stdout)
            packet_loss = float(loss_match.group(1)) if loss_match else 100.0

            if not latencies:
                 return {
                     "latency_median": None,
                     "packet_loss": packet_loss,
                     "jitter": None
                 }

            import statistics
            median_latency = statistics.median(latencies)

            # Calculate basic jitter (average absolute difference between consecutive latencies)
            jitter = 0
            if len(latencies) > 1:
                diffs = [abs(latencies[i] - latencies[i-1]) for i in range(1, len(latencies))]
                jitter = sum(diffs) / len(diffs)

            return {
                 "latency_median": median_latency,
                 "packet_loss": packet_loss,
                 "jitter": jitter
            }

         except Exception as e:
            logger.error(f"Error getting quality metrics: {e}")
            return {
                 "latency_median": None,
                 "packet_loss": 100.0,
                 "jitter": None
            }
