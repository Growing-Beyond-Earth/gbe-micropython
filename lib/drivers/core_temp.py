"""
RP2040 Internal Temperature Sensor Driver for MicroPython

This driver provides access to the RP2040 microcontroller's built-in temperature sensor
for thermal monitoring and safety protection in the GBE Box system.

The internal temperature sensor is connected to ADC4 and measures the chip temperature,
which is typically higher than ambient temperature due to internal heat generation.

Growing Beyond Earth® and this software are developed by 
Fairchild Tropical Botanic Garden, Miami, Florida, USA.

Date: September 15, 2024

For more information, visit: https://www.fairchildgarden.org/gbe
"""

import machine
import time


class CoreTemperature:
    """
    RP2040 internal temperature sensor driver.
    
    Provides access to the microcontroller's built-in temperature sensor
    for thermal monitoring and safety applications.
    
    The sensor is connected to ADC4 and uses a voltage-to-temperature
    conversion based on the RP2040 datasheet specifications.
    """
    
    def __init__(self):
        """Initialize the core temperature sensor."""
        try:
            # Initialize ADC4 for internal temperature sensor
            self._adc = machine.ADC(4)
            self._last_reading = None
            self._last_reading_time = 0
            self._reading_cache_duration = 1.0  # Cache readings for 1 second
            
            print("RP2040 core temperature sensor initialized")
            
        except Exception as e:
            print(f"Error initializing core temperature sensor: {e}")
            self._adc = None
    
    def read_temperature(self):
        """
        Read the current core temperature in Celsius.
        
        Uses the RP2040 datasheet formula for voltage-to-temperature conversion:
        Temperature = 27 - (voltage - 0.706) / 0.001721
        
        Returns:
            float: Temperature in Celsius, or None if reading fails
        """
        if not self._adc:
            return None
        
        current_time = time.time()
        
        # Use cached reading if within cache duration
        if (self._last_reading is not None and 
            current_time - self._last_reading_time < self._reading_cache_duration):
            return self._last_reading
        
        try:
            # Read raw ADC value (0-65535 for 16-bit)
            raw_reading = self._adc.read_u16()
            
            # Convert to voltage (3.3V reference)
            voltage = raw_reading * 3.3 / 65535.0
            
            # Apply RP2040 temperature conversion formula
            # Temperature = 27 - (voltage - 0.706) / 0.001721
            temperature = 27.0 - (voltage - 0.706) / 0.001721
            
            # Cache the reading
            self._last_reading = round(temperature, 1)
            self._last_reading_time = current_time
            
            return self._last_reading
            
        except Exception as e:
            print(f"Error reading core temperature: {e}")
            return None


# For testing and standalone use
if __name__ == "__main__":
    # Simple test routine
    print("Testing RP2040 Core Temperature Sensor")
    sensor = CoreTemperature()
    
    if sensor._adc:
        for i in range(5):
            temp = sensor.read_temperature()
            print(f"Reading {i+1}: {temp}°C")
            time.sleep(2)
    else:
        print("Sensor initialization failed")