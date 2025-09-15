# GROWING BEYOND EARTH CONTROL BOX
# RASPBERRY PI PICO / MICROPYTHON

# FAIRCHILD TROPICAL BOTANIC GARDEN

# This program (boot.py) runs automatically each time the device is
# powered up or rebooted.

import machine
from machine import Pin
import neopixel

# Reset hardware pins to safe state
for pinID in [0, 1, 2, 3, 4, 7]:
    p = Pin(pinID, Pin.OUT, Pin.PULL_DOWN)
    p.value(0)
    
# Turn off status LED
np = neopixel.NeoPixel(machine.Pin(6), 1)
np[0] = [0, 0, 0]
np.write()

print("Hardware ready")
