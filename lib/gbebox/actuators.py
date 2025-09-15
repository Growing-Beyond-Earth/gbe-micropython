"""
Actuator control for GBE Box (lights and fan).

Provides consistent instance-based API for hardware control.
Addresses static/instance method inconsistencies from original design.
"""

from machine import Pin, PWM
from .hardware import board


class LightController:
    """
    LED light panel controller.
    
    Manages RGBW LED channels with proper instance methods
    instead of the original static method approach.
    """
    
    def __init__(self):
        # Initialize PWM channels for each LED color
        self._rpwm = PWM(Pin(board["pins"]["red"]))
        self._gpwm = PWM(Pin(board["pins"]["green"]))
        self._bpwm = PWM(Pin(board["pins"]["blue"]))
        self._wpwm = PWM(Pin(board["pins"]["white"]))
        
        # Set PWM frequencies
        self._rpwm.freq(20000)
        self._gpwm.freq(20000)
        self._bpwm.freq(19000)
        self._wpwm.freq(19000)
        
        # Initialize all channels to off
        self._rpwm.duty_u16(0)
        self._gpwm.duty_u16(0)
        self._bpwm.duty_u16(0)
        self._wpwm.duty_u16(0)
        
        # Color channel limits (hardware-specific maximums)
        self._limits = {
            'red': 160,
            'green': 71,
            'blue': 75,
            'white': 117
        }
    
    def red(self, value=None):
        """Set or get red channel value (0-160)."""
        if value is not None:
            clamped = int(min(self._limits['red'], max(0, value)))
            self._rpwm.duty_u16(clamped * 256)
        return round(self._rpwm.duty_u16() / 256)
    
    def green(self, value=None):
        """Set or get green channel value (0-71)."""
        if value is not None:
            clamped = int(min(self._limits['green'], max(0, value)))
            self._gpwm.duty_u16(clamped * 256)
        return round(self._gpwm.duty_u16() / 256)
    
    def blue(self, value=None):
        """Set or get blue channel value (0-75)."""
        if value is not None:
            clamped = int(min(self._limits['blue'], max(0, value)))
            self._bpwm.duty_u16(clamped * 256)
        return round(self._bpwm.duty_u16() / 256)
    
    def white(self, value=None):
        """Set or get white channel value (0-117)."""
        if value is not None:
            clamped = int(min(self._limits['white'], max(0, value)))
            self._wpwm.duty_u16(clamped * 256)
        return round(self._wpwm.duty_u16() / 256)
    
    def rgbw(self, r=None, g=None, b=None, w=None):
        """Set or get all RGBW channels at once."""
        if r is not None:
            self.red(r)
        if g is not None:
            self.green(g)
        if b is not None:
            self.blue(b)
        if w is not None:
            self.white(w)
        
        return (self.red(), self.green(), self.blue(), self.white())
    
    def on(self, r=8, g=0, b=24, w=92):
        """Turn lights on with default or specified RGBW values."""
        self.rgbw(r, g, b, w)
    
    def off(self):
        """Turn all lights off."""
        self.rgbw(0, 0, 0, 0)
    
    


class FanController:
    """
    Fan speed controller.
    
    Provides instance-based fan control with proper encapsulation.
    """
    
    def __init__(self):
        self._pwm = PWM(Pin(board["pins"]["fan"]))
        self._pwm.freq(20000)
        self._pwm.duty_u16(0)
    
    def setting(self, speed=None):
        """Set or get fan speed (0-255)."""
        if speed is not None:
            clamped = int(min(255, max(0, speed)))
            self._pwm.duty_u16(clamped * 256)
        return round(self._pwm.duty_u16() / 256)
    
    def on(self, speed=96):
        """Turn fan on with default or specified speed."""
        self.setting(speed)
    
    def off(self):
        """Turn fan off."""
        self.setting(0)
    
    @property
    def speed(self):
        """Get current fan speed."""
        return self.setting()
    


# Create global instances for backward compatibility
light = LightController()
fan = FanController()