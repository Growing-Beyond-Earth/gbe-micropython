"""
Hardware Version Detection for GBE Box

Automatically detects the hardware version of the GBE Box based on:
- v1.5: Presence of ZD24C08A EEPROM module on I2C0 (addresses 0x50-0x53)
- v1.4 vs v1.0: Power consumption test with maxed LED channels

The detected version determines the correct INA219 shunt resistor value for
accurate current and power readings.
"""

import os
import time
import json
from machine import I2C, Pin


# Shunt resistor values by hardware version
RSH_BY_CLASS = {
    "v1.5": 0.0100,
    "v1.4": 0.0136, 
    "v1.0": 0.0109,
}

# Cache file path
CACHE_DIR = "/cache"
VERSION_FILE = "/cache/hardware_version.json"


class VersionDetector:
    """
    Hardware version detection for GBE Box.
    
    Detects hardware version and caches the result for future boots.
    """
    
    def __init__(self, i2c0, light_controller=None):
        """
        Initialize version detector.
        
        Args:
            i2c0: I2C bus 0 for EEPROM detection
            light_controller: LightController instance for power testing
        """
        self.i2c0 = i2c0
        self.light = light_controller
        self._version = None
        self._rsh_value = None
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        try:
            if CACHE_DIR not in os.listdir("/"):
                os.mkdir(CACHE_DIR)
        except OSError:
            pass  # Directory might already exist
    
    def _load_cached_version(self):
        """
        Load hardware version from cache file.
        
        Returns:
            dict: Version info with detection details, or None if not cached or detection was unsuccessful
        """
        try:
            with open(VERSION_FILE, 'r') as f:
                content = f.read().strip()
                
                # Try to parse as JSON first (new format)
                try:
                    cache_data = json.loads(content)
                    
                    # Validate cache structure
                    if (isinstance(cache_data, dict) and 
                        'version' in cache_data and 
                        'detection_successful' in cache_data and
                        cache_data['version'] in RSH_BY_CLASS):
                        
                        # Only use cache if detection was successful
                        if cache_data['detection_successful']:
                            return cache_data
                            
                except ValueError:
                    # Fall back to old text format for backward compatibility
                    if content in RSH_BY_CLASS:
                        # Convert old format to new format and re-save
                        cache_data = {
                            "version": content,
                            "detection_successful": True,  # Assume old cache was successful
                            "detection_method": "Legacy cache",
                            "detection_timestamp": time.time(),
                            "rsh_value": RSH_BY_CLASS[content],
                            "notes": "Converted from legacy text cache"
                        }
                        
                        # Re-save in new format  
                        try:
                            # Try to use jpretty for better formatting
                            try:
                                from json_utils import jpretty
                                formatted_data = jpretty.jpretty(cache_data)
                                with open(VERSION_FILE, 'w') as f_write:
                                    f_write.write(formatted_data)
                            except ImportError:
                                # Fall back to standard json if jpretty not available
                                with open(VERSION_FILE, 'w') as f_write:
                                    json.dump(cache_data, f_write)
                        except OSError:
                            pass
                            
                        return cache_data
                    
        except (OSError, ValueError):
            pass
        return None
    
    def _save_version_to_cache(self, version, detection_successful, detection_method=None, notes=None):
        """
        Save detected hardware version to cache file with detection details.
        
        Args:
            version (str): Hardware version detected
            detection_successful (bool): Whether detection was definitive
            detection_method (str): How the version was detected
            notes (str): Additional information about detection
        """
        self._ensure_cache_dir()
        try:
            cache_data = {
                "version": version,
                "detection_successful": detection_successful,
                "detection_method": detection_method,
                "detection_timestamp": time.time(),
                "rsh_value": RSH_BY_CLASS[version],
                "notes": notes
            }
            
            # Try to use jpretty for better formatting
            try:
                from json_utils import jpretty
                formatted_data = jpretty.jpretty(cache_data)
                with open(VERSION_FILE, 'w') as f:
                    f.write(formatted_data)
            except ImportError:
                # Fall back to standard json if jpretty not available
                with open(VERSION_FILE, 'w') as f:
                    json.dump(cache_data, f)
        except OSError:
            pass  # Silently fail if cache can't be written
    
    def _detect_eeprom_v15(self):
        """
        Detect v1.5 hardware by checking for ZD24C08A EEPROM module.
        
        v1.5 boards have an EEPROM on I2C0 with addresses 0x50, 0x51, 0x52, 0x53.
        
        Returns:
            tuple: (success: bool, found_addresses: list)
        """
        if not self.i2c0:
            return False, []
        
        eeprom_addresses = [0x50, 0x51, 0x52, 0x53]
        
        try:
            # Scan I2C bus for EEPROM addresses
            devices = self.i2c0.scan()
            
            # Check which EEPROM addresses are present
            found_addresses = [addr for addr in eeprom_addresses if addr in devices]
            
            # Return success if any EEPROM addresses found
            return len(found_addresses) > 0, found_addresses
            
        except Exception:
            return False, []
    
    def _detect_v14_vs_v10_power_test(self):
        """
        Differentiate v1.4 vs v1.0 using power consumption test.
        
        Sets shunt resistor to 0.0100 and maxes out LED channels.
        - v1.4: Registers >70W (due to 60W PSU limitation)
        - v1.0: Registers ~63W
        
        Returns:
            tuple: (version: str, success: bool, avg_power: float, notes: str)
        """
        if not self.light:
            return "v1.0", False, 0.0, "No light controller available for power test"
        
        try:
            # First check if 24V power is present
            import gbebox
            initial_voltage = gbebox.sensor.voltage()
            
            if initial_voltage is None or initial_voltage < 20:
                return "v1.0", False, 0.0, f"Power test failed: insufficient voltage ({initial_voltage}V) - 24V power required"
            
            # Save current LED state
            original_rgbw = self.light.rgbw()
            
            # Set all LED channels to maximum safe values
            # These are the hardware limits from actuators.py
            max_red = 160
            max_green = 71  
            max_blue = 75
            max_white = 117
            
            self.light.rgbw(max_red, max_green, max_blue, max_white)
            
            # Wait for power readings to stabilize
            time.sleep(3)
            
            # Take power readings with default RSH=0.01 calibration
            # v1.4 boards will read erroneously high (>70W) due to incorrect RSH
            # v1.0 boards will read more accurately (~60-65W)
            power_readings = []
            voltage_readings = []
            
            for i in range(5):
                try:
                    power = gbebox.sensor.power()
                    voltage = gbebox.sensor.voltage()
                    
                    if power is not None:
                        power_readings.append(power)
                    if voltage is not None:
                        voltage_readings.append(voltage)
                        
                except Exception:
                    pass
                    
                time.sleep(0.5)
            
            # Restore original LED state
            self.light.rgbw(*original_rgbw)
            
            if power_readings:
                avg_power = sum(power_readings) / len(power_readings)
                avg_voltage = sum(voltage_readings) / len(voltage_readings) if voltage_readings else 0
                
                # Check if we got meaningful power readings (should be >40W with lights on)
                if avg_power < 40:
                    return "v1.0", False, avg_power, f"Power test failed: only {avg_power:.1f}W detected, need >40W for reliable detection"
                
                # Differentiate based on power consumption with default RSH=0.01
                if avg_power > 70:
                    return "v1.4", True, avg_power, f"Power test successful: {avg_power:.1f}W with wrong RSH indicates v1.4"
                else:
                    return "v1.0", True, avg_power, f"Power test successful: {avg_power:.1f}W indicates v1.0"
            else:
                avg_voltage = sum(voltage_readings) / len(voltage_readings) if voltage_readings else 0
                return "v1.0", False, 0.0, f"No power readings (voltage readings: {len(voltage_readings)}, avg: {avg_voltage:.1f}V)"
                
        except Exception as e:
            # Restore LEDs if something went wrong
            try:
                if self.light:
                    self.light.off()
            except:
                pass
            return "v1.0", False, 0.0, f"Power test failed due to exception: {e}"
    
    def detect_version(self, force_detect=False):
        """
        Detect hardware version with caching.
        
        Args:
            force_detect (bool): If True, skip cache and force new detection
            
        Returns:
            str: Hardware version ("v1.5", "v1.4", or "v1.0")
        """
        # Check cache first unless forcing detection
        if not force_detect:
            cached_data = self._load_cached_version()
            if cached_data:
                self._version = cached_data['version']
                self._rsh_value = RSH_BY_CLASS[self._version]
                return self._version
            elif self.should_retry_detection():
                # Previous detection was unsuccessful, retry
                force_detect = True
        
        # Step 1: Check for v1.5 EEPROM
        eeprom_found, found_addresses = self._detect_eeprom_v15()
        if eeprom_found:
            version = "v1.5"
            detection_successful = True
            detection_method = "EEPROM detection"
            notes = f"Found EEPROM at addresses: {[hex(addr) for addr in found_addresses]}"
        else:
            # Step 2: Differentiate v1.4 vs v1.0 using power test
            version, detection_successful, avg_power, power_notes = self._detect_v14_vs_v10_power_test()
            detection_method = "Power consumption test"
            notes = power_notes
        
        # Cache the result with detection details
        self._save_version_to_cache(version, detection_successful, detection_method, notes)
        
        self._version = version
        self._rsh_value = RSH_BY_CLASS[version]
        
        return version
    
    @property
    def version(self):
        """Get the detected hardware version."""
        if self._version is None:
            self.detect_version()
        return self._version
    
    @property 
    def rsh_value(self):
        """Get the shunt resistor value for this hardware version."""
        if self._rsh_value is None:
            self.detect_version()
        return self._rsh_value
    
    def should_retry_detection(self):
        """
        Check if detection should be retried based on previous failed attempts.
        
        Returns:
            bool: True if detection should be retried
        """
        try:
            with open(VERSION_FILE, 'r') as f:
                cache_data = json.load(f)
                
                # Retry if previous detection was unsuccessful
                if not cache_data.get('detection_successful', True):
                    return True
                    
        except (OSError, ValueError):
            # No cache file or invalid format - should detect
            return True
            
        return False
    
    
    def force_redetection(self):
        """Force re-detection of hardware version (ignores cache)."""
        return self.detect_version(force_detect=True)
    
    def get_detection_info(self):
        """
        Get detailed information about the last detection attempt.
        
        Returns:
            dict: Detection information or None if no cache exists
        """
        try:
            with open(VERSION_FILE, 'r') as f:
                return json.load(f)
        except (OSError, ValueError):
            return None


# Global instance (will be initialized by hardware.py)
version_detector = None