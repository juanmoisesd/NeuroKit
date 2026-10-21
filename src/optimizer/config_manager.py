import subprocess
import platform
import logging

logger = logging.getLogger(__name__)

class OptimizerMode:
    DIAGNOSTIC = 1
    RECOMMENDATION = 2
    OPTIMIZATION = 3

class ConfigManager:
    def __init__(self, db_manager):
        self.is_windows = platform.system().lower() == "windows"
        self.db_manager = db_manager
        self.mode = OptimizerMode.RECOMMENDATION

        # Known properties that can often be optimized
        self.known_properties = {
             "RoamingAggressiveness": {
                  "desc": "How aggressively the adapter searches for other access points.",
                  "conservative": "Medium-Low",
                  "performance": "Medium",
                  "roaming": "Highest"
             },
             "TransmitPower": {
                  "desc": "Transmit power of the Wi-Fi adapter.",
                  "conservative": "Medium",
                  "performance": "Highest"
             },
             "PreferredBand": {
                  "desc": "Prefer 5GHz or 2.4GHz connections.",
                  "performance": "Prefer 5GHz band"
             }
        }

    def set_mode(self, mode):
        self.mode = mode

    def get_recommendations(self, adapter_name, current_properties):
        """Generate recommendations based on current properties."""
        recommendations = []

        for prop, details in self.known_properties.items():
             if prop in current_properties:
                  current_val = current_properties[prop]

                  if prop == "TransmitPower" and current_val != details["performance"]:
                       recommendations.append({
                            "property": prop,
                            "current": current_val,
                            "proposed": details["performance"],
                            "reason": "Maximizes signal strength and connection stability.",
                            "benefit": "Better range and fewer drops.",
                            "side_effect": "Slightly higher power consumption."
                       })

                  if prop == "PreferredBand" and current_val != details["performance"]:
                       recommendations.append({
                            "property": prop,
                            "current": current_val,
                            "proposed": details["performance"],
                            "reason": "5GHz offers higher speeds and less interference.",
                            "benefit": "Faster throughput.",
                            "side_effect": "Shorter range compared to 2.4GHz."
                       })

        return recommendations

    def apply_optimization(self, adapter_name, property_name, new_value, current_value):
        """Apply a configuration change if in mode 3."""
        if self.mode != OptimizerMode.OPTIMIZATION:
             logger.warning(f"Cannot apply optimization. Mode is {self.mode}")
             return False, "Application is not in Optimization mode."

        if not self.is_windows:
             logger.info(f"Mocking optimization: set {property_name} to {new_value} on {adapter_name}")
             self.db_manager.record_config_change(adapter_name, property_name, current_value, new_value)
             return True, "Success (Mocked)"

        # Secure PowerShell invocation using arguments array instead of direct string formatting
        cmd = [
             "powershell", "-NoProfile", "-Command",
             "param($adapter, $prop, $val) Set-NetAdapterAdvancedProperty -Name $adapter -DisplayName $prop -DisplayValue $val",
             "-adapter", adapter_name,
             "-prop", property_name,
             "-val", new_value
        ]

        try:
             # Capture state before change
             self.db_manager.record_config_change(adapter_name, property_name, current_value, new_value)

             creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

             result = subprocess.run(
                  cmd,
                  capture_output=True,
                  text=True,
                  creationflags=creationflags
             )

             if result.returncode == 0:
                  return True, "Optimization applied successfully."
             else:
                  logger.error(f"Failed to apply optimization: {result.stderr}")
                  return False, f"Failed: {result.stderr.strip()}"

        except Exception as e:
             logger.error(f"Error applying optimization: {e}")
             return False, str(e)

    def revert_optimization(self, config_change_id):
         """Revert a specific change by ID."""
         if self.mode != OptimizerMode.OPTIMIZATION:
             return False, "Not in Optimization mode."

         history = self.db_manager.get_config_history()
         change = next((c for c in history if c["id"] == config_change_id), None)

         if not change:
              return False, "Change record not found."

         adapter = change["adapter_name"]
         prop = change["property_name"]
         old_val = change["old_value"]

         if not self.is_windows:
              logger.info(f"Mocking reversion: set {prop} back to {old_val} on {adapter}")
              return True, "Reverted successfully (Mocked)"

         cmd = [
             "powershell", "-NoProfile", "-Command",
             "param($adapter, $prop, $val) Set-NetAdapterAdvancedProperty -Name $adapter -DisplayName $prop -DisplayValue $val",
             "-adapter", adapter,
             "-prop", prop,
             "-val", old_val
         ]

         try:
             creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
             result = subprocess.run(
                  cmd,
                  capture_output=True,
                  text=True,
                  creationflags=creationflags
             )

             if result.returncode == 0:
                  self.db_manager.log_event("REVERT", f"Reverted {prop} on {adapter} to {old_val}")
                  return True, "Reverted successfully."
             else:
                  return False, f"Failed to revert: {result.stderr}"
         except Exception as e:
              return False, str(e)
