"""
FanRPM MicroPython Library

This library provides a class for measuring the RPM (Revolutions Per Minute) of a fan using a tachometer sensor 
connected to a Raspberry Pi Pico or other MicroPython-compatible microcontroller. It captures tachometer pulses, 
calculates RPM based on the specified pulses per revolution, and provides real-time fan speed data. The library 
is designed to be part of the Growing Beyond Earth(R) Control Box project, where precise control and monitoring 
of fan speeds is critical for environmental management.

Growing Beyond Earth(R) and this software are developed by Fairchild Tropical Botanic Garden, Miami, Florida, USA.

Date: September 14, 2024

For more information, visit: https://www.fairchildgarden.org/gbe
"""

from machine import Pin, Timer

class FanRPM:
    def __init__(self, pin_num, pulses_per_rev=2, calc_interval=1):
        self.tach_pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self.pulses_per_rev = pulses_per_rev
        self.calc_interval = calc_interval
        self.pulse_count = 0
        self.rpm = 0
        self.timer = Timer()

        # Attach the interrupt to the tachometer pin
        self.tach_pin.irq(trigger=Pin.IRQ_FALLING, handler=self._tachometer_callback)

        # Setup the timer to calculate RPM periodically
        self.timer.init(freq=1/self.calc_interval, mode=Timer.PERIODIC, callback=self._calculate_rpm)

    def _tachometer_callback(self, pin):
        self.pulse_count += 1

    def _calculate_rpm(self, timer):
        # Calculate RPM based on the number of pulses counted
        self.rpm = int((self.pulse_count / self.pulses_per_rev) * (60 / self.calc_interval))
        self.pulse_count = 0

    def get_rpm(self):
        return self.rpm

    def stop(self):
        # Stop the timer when no longer needed
        self.timer.deinit()
