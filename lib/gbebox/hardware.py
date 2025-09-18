"""
Hardware abstraction layer for GBE Box.

Manages board configuration, pin definitions, and hardware interfaces.
"""

import machine
from machine import Pin, I2C, SPI
import json
import ubinascii
import network


class BoardConfig:
    """Manages board configuration and hardware interfaces."""
    
    def __init__(self, config_file="board.json"):
        self.config = self._load_board_config(config_file)
        self.id = self._get_board_id()
        self.mac = self._get_mac_address()
        
        # Initialize hardware interfaces
        self.i2c0 = I2C(0, sda=Pin(self.config["pins"]["i2c0_sda"]), 
                           scl=Pin(self.config["pins"]["i2c0_scl"]))
        self.i2c1 = I2C(1, sda=Pin(self.config["pins"]["i2c1_sda"]), 
                           scl=Pin(self.config["pins"]["i2c1_scl"]))
        self.spi0 = SPI(0, baudrate=40000000,
                           sck=Pin(self.config["pins"]["spi0_sck"]),
                           mosi=Pin(self.config["pins"]["spi0_mosi"]),
                           miso=Pin(self.config["pins"]["spi0_miso"]))
        self.led = Pin(self.config["pins"]["led"], Pin.OUT)
        
    
    def _load_board_config(self, filename):
        """Load board configuration from JSON file."""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading board configuration: {e}")
            return {}
    
    def _get_board_id(self):
        """Get unique board identifier."""
        try:
            return ubinascii.hexlify(machine.unique_id()).decode()
        except Exception as e:
            print(f"Error reading board ID: {e}")
            return None
    
    def _get_mac_address(self):
        """Get MAC address."""
        try:
            return ubinascii.hexlify(network.WLAN().config("mac"), ":").decode()
        except Exception as e:
            print(f"Error reading MAC address: {e}")
            return None
    
    def usb_connected(self):
        """Check if USB port is connected to a computer."""
        SIE_STATUS = 0x50110000 + 0x50
        CONNECTED = 1 << 16
        SUSPENDED = 1 << 4
        
        status = machine.mem32[SIE_STATUS] & (CONNECTED | SUSPENDED)
        return status == CONNECTED
    
    
    

# Create global board instance
board_config = BoardConfig()

# Export for backward compatibility
board = {
    "model": board_config.config.get("model"),
    "default_year": board_config.config.get("default_year"),
    "pins": board_config.config.get("pins", {}),
    "id": board_config.id,
    "mac": board_config.mac
}

# Export hardware interfaces
i2c0 = board_config.i2c0
i2c1 = board_config.i2c1
spi0 = board_config.spi0
led = board_config.led
usb_connected = board_config.usb_connected


def detect_and_configure_hardware():
    """
    Detect hardware version and configure sensors accordingly.
    
    This should be called after gbebox is imported but before any
    significant sensor operations that require accurate power readings.
    
    Returns:
        dict: Detection results with version info, or None if detection fails
    """
    try:
        from drivers.version_detect import VersionDetector
        from . import sensor, light
        
        # Create version detector with all necessary components
        version_detector = VersionDetector(i2c0, light_controller=light)
        
        # Perform detection
        detected_version = version_detector.detect_version()
        rsh_value = version_detector.rsh_value
        
        # Get detection details for logging
        detection_info = version_detector.get_detection_info()
        
        return {
            'version': detected_version,
            'rsh_value': rsh_value,
            'detection_info': detection_info
        }
        
    except Exception as e:
        print(f"Hardware version detection failed: {e}")
        return None


def get_hardware_info():
    """
    Get comprehensive hardware information including version detection.
    
    Returns:
        dict: Hardware information
    """
    try:
        from drivers.version_detect import VersionDetector
        
        # Try to get cached detection info first
        version_detector = VersionDetector(i2c0, light_controller=None)
        detection_info = version_detector.get_detection_info()
        
        if detection_info:
            hardware_version = detection_info.get('version', 'unknown')
            rsh_value = detection_info.get('rsh_value', 0.0100)
            detection_successful = detection_info.get('detection_successful', False)
        else:
            hardware_version = 'unknown'
            rsh_value = 0.0100
            detection_successful = False
        
        return {
            'hardware_version': hardware_version,
            'rsh_value': rsh_value,
            'detection_successful': detection_successful,
            'board_id': board.get('id', 'unknown'),
            'mac_address': board.get('mac', 'unknown'),
            'usb_connected': usb_connected(),
            'full_detection_info': detection_info
        }
        
    except Exception:
        return {
            'hardware_version': 'unknown',
            'rsh_value': 0.0100,
            'detection_successful': False,
            'board_id': board.get('id', 'unknown'),
            'mac_address': board.get('mac', 'unknown'),
            'usb_connected': usb_connected(),
            'full_detection_info': None
        }


def force_hardware_redetection():
    """
    Force a fresh hardware version detection, ignoring cache.
    
    Returns:
        dict: Detection results, or None if detection fails
    """
    try:
        from drivers.version_detect import VersionDetector
        from . import sensor, light
        
        version_detector = VersionDetector(i2c0, light_controller=light)
        detected_version = version_detector.force_redetection()
        rsh_value = version_detector.rsh_value
        
        detection_info = version_detector.get_detection_info()
        
        return {
            'version': detected_version,
            'rsh_value': rsh_value,
            'detection_info': detection_info
        }
        
    except Exception as e:
        print(f"Hardware redetection failed: {e}")
        return None


class SystemUtils:
    """System-level utility functions for runtime detection and diagnostics."""
    
    @staticmethod
    def display_system_info():
        """Display system information including hardware ID, network info, and available sensors."""
        # Import at function level to avoid circular imports
        from .networking import wlan  
        from .sensors import sensor
        
        # Display hardware version information
        try:
            hw_info = get_hardware_info()
            if hw_info and hw_info.get('detection_successful', False):
                version = hw_info.get('hardware_version', 'unknown')
                # Hardware version to date mapping
                version_dates = {
                    "v1.0": "2024-08-07",
                    "v1.4": "2025-08-11", 
                    "v1.5": "2025-09-01"
                }
                hardware_date = version_dates.get(version, "unknown")
                print(f"Hardware:       {version} ({hardware_date})")
        except Exception:
            # If hardware detection info isn't available, continue without it
            pass
            
        print("Hardware ID:    " + board["id"])
        if board["mac"]:
            print("MAC address:    " + board["mac"])
            
        if wlan.ifconfig()[0]:     
            print("IP Address:     " + wlan.ifconfig()[0] + "\n")
        
        print("Available Sensors:")
        for sensor_info in sensor.get_available_sensors():
            print(sensor_info)
        print()


# Create global instance for backward compatibility
system = SystemUtils()