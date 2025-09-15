"""
Growing Beyond Earth (GBE) Box Control Library

This library provides a unified interface for controlling the GBE Box hardware,
including environmental sensors, LED lighting, fans, and other components.

Growing Beyond Earth® and this software are developed by 
Fairchild Tropical Botanic Garden, Miami, Florida, USA.

For more information, visit: https://www.fairchildgarden.org/gbe
"""

# Software version information
def _load_version():
    """Load software version from version.txt file."""
    try:
        with open('/version.txt', 'r') as f:
            return f.read().strip()
    except Exception:
        # Fallback version if file doesn't exist
        return "2025-09-08"

software_date = _load_version()

# Import all modules to create the unified API
from .hardware import (
    board, i2c0, i2c1, spi0, led, usb_connected, board_config
)

from .sensors import sensor

from .actuators import light, fan

from .indicator import indicator

from .storage import sd

from .networking import wifi, wlan

from .clock import clock

# Import application logic and utilities
from application import calc, system, Run, ProgramEngine, WatchdogManager, GarbageCollector, DataLogger

# Import built-in libraries commonly used by student programs
import time
import uasyncio as asyncio

# For backward compatibility with student programs, export commonly used modules
__all__ = [
    # Hardware
    'board', 'i2c0', 'i2c1', 'spi0', 'led', 'usb_connected',
    
    # Sensors
    'sensor',
    
    # Actuators  
    'light', 'fan',
    
    # Status
    'indicator',
    
    # Storage
    'sd',
    
    # Networking
    'wifi', 'wlan',
    
    # Time
    'clock',
    
    # Utilities
    'calc', 'system',
    
    # Program execution
    'Run', 'ProgramEngine',
    
    # Version info
    'software_date',
    
    # Common imports for convenience
    'time', 'asyncio'
]


def get_system_info():
    """Get system information including memory usage."""
    import gc
    memory_info = sensor.get_memory_usage()
    return {
        'software_date': software_date,
        'board_id': board.get('id', 'Unknown'),
        'memory': memory_info,
        'sensors_available': len(sensor.get_available_sensors())
    }

# Print initialization message when imported
print(f"GBE Box Library loaded - Software date: {software_date}")
print("Hardware abstraction initialized")