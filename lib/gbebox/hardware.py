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