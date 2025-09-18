"""
Actuator control for GBE Box (lights and fan).

Provides consistent instance-based API for hardware control.
Addresses static/instance method inconsistencies from original design.
"""

import time
import uasyncio as asyncio
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
        
        # Power-based control state tracking
        self._last_power_target = None
        self._last_power_result = None
    
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
            
        # Clear power control cache when manually setting PWM values
        if r is not None or g is not None or b is not None or w is not None:
            self._last_power_target = None
            self._last_power_result = None
        
        return (self.red(), self.green(), self.blue(), self.white())
    
    def on(self, r=8, g=0, b=24, w=92):
        """Turn lights on with default or specified RGBW values."""
        self.rgbw(r, g, b, w)
    
    def off(self):
        """Turn all lights off."""
        self.rgbw(0, 0, 0, 0)
    
    async def set_rgbw_with_power_target(self, r, g, b, w, target_watts, tolerance=0.5, max_iterations=5):
        """
        Set RGBW channels to achieve a target power consumption.
        
        Uses iterative adjustment to scale PWM values until actual power consumption
        matches the target within the specified tolerance.
        
        Args:
            r, g, b, w (int): Initial PWM values for red, green, blue, white channels
            target_watts (float): Target power consumption in watts
            tolerance (float): Acceptable power difference in watts (default 0.5W)
            max_iterations (int): Maximum adjustment iterations (default 5)
            
        Returns:
            dict: Results with final PWM values, actual power, and success status
        """
        # Check if we already have a successful result for this target
        if (self._last_power_target == target_watts and 
            self._last_power_result is not None and 
            self._last_power_result.get('success', False)):
            
            # Use the previous successful result (no need to copy since we don't modify it)
            self.rgbw(*self._last_power_result['final_rgbw'])
            return self._last_power_result
        
        # Validate inputs
        if target_watts <= 0:
            return {
                'success': False, 
                'error': 'Target watts must be positive',
                'final_rgbw': (r, g, b, w),
                'actual_power': 0
            }
        
        if target_watts < 2:
            return {
                'success': False,
                'error': 'Target watts too low for reliable power measurement (minimum 2W)',
                'final_rgbw': (r, g, b, w), 
                'actual_power': 0
            }
        
        # Check if power sensor is available and initial conditions
        try:
            from gbebox.sensors import sensor
            
            # Check voltage first - need sufficient power supply
            voltage = sensor.voltage()
            if voltage is None or voltage < 20:
                self.rgbw(r, g, b, w)
                return {
                    'success': False,
                    'error': f'Insufficient voltage for power control: {voltage}V (need >20V)',
                    'final_rgbw': (r, g, b, w),
                    'actual_power': None
                }
            
            # Test if we can get initial power reading
            initial_power = sensor.power()
            if initial_power is None:
                # Fall back to standard PWM control if no power sensor
                self.rgbw(r, g, b, w)
                return {
                    'success': False,
                    'error': 'Power sensor not available, using PWM-only control',
                    'final_rgbw': (r, g, b, w),
                    'actual_power': None
                }
                
        except Exception as e:
            self.rgbw(r, g, b, w)
            return {
                'success': False,
                'error': f'Sensor error: {e}',
                'final_rgbw': (r, g, b, w),
                'actual_power': None
            }
        
        # Start iterative adjustment
        current_r, current_g, current_b, current_w = r, g, b, w
        
        # Apply initial PWM values first to turn on lights
        self.rgbw(current_r, current_g, current_b, current_w)
        
        # Wait for initial stabilization
        await asyncio.sleep(3.0)
        
        for iteration in range(max_iterations):
            # Get actual power consumption with multiple attempts
            actual_power = None
            for attempt in range(3):
                try:
                    reading = sensor.power()
                    if reading is not None and reading > 0:
                        actual_power = reading
                        break
                    else:
                        await asyncio.sleep(0.5)  # Brief wait between attempts
                except Exception:
                    await asyncio.sleep(0.5)
            
            if actual_power is None or actual_power <= 0:
                return {
                    'success': False,
                    'error': f'Unable to get valid power reading after multiple attempts on iteration {iteration + 1}',
                    'final_rgbw': (current_r, current_g, current_b, current_w),
                    'actual_power': actual_power
                }
            
            # Check if we're within tolerance
            power_diff = abs(actual_power - target_watts)
            if power_diff <= tolerance:
                # Store successful result for future use
                result = {
                    'success': True,
                    'iterations': iteration + 1,
                    'final_rgbw': (current_r, current_g, current_b, current_w),
                    'actual_power': actual_power,
                    'target_power': target_watts,
                    'power_diff': power_diff
                }
                self._last_power_target = target_watts
                self._last_power_result = result
                return result
            
            # Calculate scaling factor for next iteration
            if actual_power > 0:
                scale_factor = target_watts / actual_power
                
                # Apply scaling with hardware limits
                new_r = min(self._limits['red'], max(0, int(current_r * scale_factor)))
                new_g = min(self._limits['green'], max(0, int(current_g * scale_factor)))
                new_b = min(self._limits['blue'], max(0, int(current_b * scale_factor)))
                new_w = min(self._limits['white'], max(0, int(current_w * scale_factor)))
                
                # Check if we've hit hardware limits and can't scale further
                if (new_r == current_r and new_g == current_g and 
                    new_b == current_b and new_w == current_w):
                    return {
                        'success': False,
                        'error': f'Hardware limits reached, cannot achieve {target_watts}W',
                        'iterations': iteration + 1,
                        'final_rgbw': (current_r, current_g, current_b, current_w),
                        'actual_power': actual_power,
                        'target_power': target_watts,
                        'max_possible_power': actual_power
                    }
                
                current_r, current_g, current_b, current_w = new_r, new_g, new_b, new_w
                
                # Apply new PWM values for next iteration
                self.rgbw(current_r, current_g, current_b, current_w)
                await asyncio.sleep(2.5)  # Wait for stabilization
        
        # Maximum iterations reached
        return {
            'success': False,
            'error': f'Max iterations ({max_iterations}) reached without convergence',
            'iterations': max_iterations,
            'final_rgbw': (current_r, current_g, current_b, current_w),
            'actual_power': actual_power,
            'target_power': target_watts,
            'power_diff': abs(actual_power - target_watts)
        }


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