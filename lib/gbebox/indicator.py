"""
Status indicator control for GBE Box.

Manages the NeoPixel status LED with consistent instance-based API.
"""

import uasyncio as asyncio
import neopixel
from machine import Pin
from .hardware import board


class StatusIndicator:
    """
    NeoPixel status indicator controller.
    
    Provides visual feedback for system status through color-coded LED patterns.
    """
    
    # Color definitions (RGB values normalized to 0-1)
    COLORS = {
        "red": [1, 0, 0],
        "green": [0, 1, 0],
        "blue": [0, 0, 1],
        "yellow": [1, 0.6, 0],
        "cyan": [0, 0.8, 0.8],
        "magenta": [0.8, 0, 0.8],
        "white": [0.6, 0.6, 0.6],
    }
    
    def __init__(self):
        self._np = neopixel.NeoPixel(Pin(board["pins"]["neopixel"]), 1)
        self.off()  # Start with LED off
    
    def on(self, color="white"):
        """Turn on the indicator with specified color."""
        if color in self.COLORS:
            rgb_values = tuple(int(rgb * 255) for rgb in self.COLORS[color])
            self._np[0] = rgb_values
            self._np.write()
    
    def off(self):
        """Turn off the indicator."""
        self._np[0] = (0, 0, 0)
        self._np.write()
    
    async def pulse(self, color="white", duration=2):
        """Create a breathing/pulse effect with the specified color."""
        if color not in self.COLORS:
            color = "white"
        
        steps = 255
        step_duration = duration / (2 * steps)
        
        # Fade in
        for val in range(steps + 1):
            rgb_values = tuple(int(rgb * val) for rgb in self.COLORS[color])
            self._np[0] = rgb_values
            self._np.write()
            await asyncio.sleep(step_duration)
        
        # Fade out
        for val in range(steps, -1, -1):
            rgb_values = tuple(int(rgb * val) for rgb in self.COLORS[color])
            self._np[0] = rgb_values
            self._np.write()
            await asyncio.sleep(step_duration)
    
    async def solid(self, color="white", duration=None):
        """Show solid color for specified duration (or indefinitely if None)."""
        self.on(color)
        if duration is not None:
            await asyncio.sleep(duration)
            self.off()
    
    async def blink(self, color="white", interval=1):
        """Blink the indicator continuously."""
        while True:
            await self.pulse(color)
            await asyncio.sleep(interval)
    
    async def status(self):
        """
        Show system status through color patterns.
        
        Priority order (highest to lowest):
        - Red solid: Thermal shutdown active (overrides everything)
        - Blue pulse: SD card mounted and WiFi connected
        - White pulse: SD card mounted, no WiFi
        - Yellow pulse: No SD card
        """
        # Import here to avoid circular dependencies
        from .storage import sd
        from .networking import wlan
        
        while True:
            # Status patterns
            if sd.mount():
                if wlan.isconnected():
                    await self.pulse("blue")
                else:
                    await self.pulse("white")
            else:
                await self.pulse("yellow")
            await asyncio.sleep(1)


# Create global instance
indicator = StatusIndicator()