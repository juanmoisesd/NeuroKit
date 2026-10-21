import time
import logging
from threading import Thread, Event
from src.network.connectivity import ConnectivityChecker
from src.network.adapter import NetworkAdapter

logger = logging.getLogger(__name__)

class MonitoringEngine:
    def __init__(self, db_manager, interval=60):
        self.db_manager = db_manager
        self.interval = interval
        self.checker = ConnectivityChecker()
        self.adapter = NetworkAdapter()
        self._stop_event = Event()
        self._thread = None
        self.last_status = {}

    def start(self):
        """Start the monitoring background thread."""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            logger.info("Monitoring engine started.")

    def stop(self):
        """Stop the monitoring background thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
            logger.info("Monitoring engine stopped.")

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            self._run_checks()
            # Wait for the interval, but allow quick exit if stop is called
            self._stop_event.wait(self.interval)

    def _run_checks(self):
        """Run all network checks and record results."""
        try:
            interfaces = self.adapter.get_interfaces()
            if not interfaces:
                 if self.last_status.get("adapter_connected", True):
                      self.db_manager.log_event("ADAPTER_ERROR", "No active Wi-Fi interfaces found.")
                      self.last_status["adapter_connected"] = False
                 return

            self.last_status["adapter_connected"] = True
            active_iface = interfaces[0]

            ip_config = self.adapter.get_ip_config(active_iface.get("name", "Wi-Fi"))
            gateway = ip_config.get("gateway")

            # Basic connectivity checks
            gateway_ok, gw_latency = self.checker.check_local_gateway(gateway)
            dns_ok, _ = self.checker.check_dns_resolution()
            internet_ok, _ = self.checker.check_internet_access()

            # Detailed quality metrics
            quality = self.checker.get_quality_metrics()

            # Record metrics
            self.db_manager.insert_metric(
                latency_median=quality.get("latency_median"),
                packet_loss=quality.get("packet_loss"),
                jitter=quality.get("jitter"),
                ssid=active_iface.get("ssid"),
                signal=active_iface.get("signal")
            )

            # Intelligent diagnostic rules
            self._analyze_status(gateway_ok, dns_ok, internet_ok, quality, active_iface)

        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")

    def _analyze_status(self, gateway_ok, dns_ok, internet_ok, quality, iface):
        """Apply rules to detect issues."""
        ssid = iface.get("ssid", "Unknown")

        # Rule 1: Local vs Internet issue
        if not gateway_ok:
             self.db_manager.log_event("DEGRADED", f"Cannot reach local gateway on {ssid}")
        elif gateway_ok and not dns_ok:
             self.db_manager.log_event("DEGRADED", "DNS resolution failing, local network OK")
        elif gateway_ok and dns_ok and not internet_ok:
             self.db_manager.log_event("DEGRADED", "Internet access failing, DNS and local OK")

        # Rule 2: Quality degradation
        packet_loss = quality.get("packet_loss")
        if packet_loss is not None and packet_loss > 10.0:
             self.db_manager.log_event("QUALITY_DROP", f"High packet loss detected: {packet_loss}%")

        latency = quality.get("latency_median")
        if latency is not None and latency > 150.0:
             self.db_manager.log_event("QUALITY_DROP", f"High latency detected: {latency}ms")
