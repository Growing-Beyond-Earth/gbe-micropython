# GROWING BEYOND EARTH CONTROL BOX
# RASPBERRY PI PICO / MICROPYTHON
# FAIRCHILD TROPICAL BOTANIC GARDEN

# This program (boot.py) runs automatically each time the device is powered up or rebooted.

import machine
from machine import Pin
import time
import neopixel
import json

# Load board configuration
with open('board.json', 'r') as f:
    board = json.load(f)

# --- I2C bus recovery (run BEFORE any I2C() is constructed) ---

def i2c_bus_recover(scl_pin_num: int, sda_pin_num: int, pulses: int = 16, t_us: int = 6) -> bool:
    """
    Try to free a stuck I2C bus by pulsing SCL and issuing a STOP.
    Succeeds only if BOTH SCL and SDA read high at the end.
    """
    from machine import Pin
    import time

    # Release-high (open-drain for SDA; push-pull high for SCL is OK for clocking)
    scl = Pin(scl_pin_num, Pin.OUT, value=1)
    sda = Pin(sda_pin_num, Pin.OPEN_DRAIN, value=1)
    time.sleep_us(t_us)

    # If SCL is being held low, recovery is unlikely—wiggle SDA a bit, then bail quickly
    if scl.value() == 0:
        for _ in range(4):
            sda.off(); time.sleep_us(t_us)
            sda.on();  time.sleep_us(t_us)
            if scl.value(): break
        try:
            scl.init(Pin.IN, Pin.PULL_UP); sda.init(Pin.IN, Pin.PULL_UP)
        except Exception:
            pass
        return (scl.value() == 1) and (sda.value() == 1)

    # SCL is high. If SDA is low, clock up to `pulses` times to let a slave finish a byte
    if sda.value() == 0:
        for _ in range(pulses):
            scl.off(); time.sleep_us(t_us)
            scl.on();  time.sleep_us(t_us)
            if sda.value():  # released
                break

    # Generate a STOP: SDA low -> SCL high -> SDA high
    sda.off(); time.sleep_us(t_us)
    scl.on();  time.sleep_us(t_us)
    sda.on();  time.sleep_us(t_us)

    # Return pins to inputs with pull-ups
    try:
        scl.init(Pin.IN, Pin.PULL_UP); sda.init(Pin.IN, Pin.PULL_UP)
    except Exception:
        pass

    return (scl.value() == 1) and (sda.value() == 1)

# --- Reset hardware pins to safe state ---

for pinID in [0, 1, 2, 3, 4, 7]:
    p = Pin(pinID, Pin.OUT, Pin.PULL_DOWN)
    p.value(0)

# Turn off status LED
np = neopixel.NeoPixel(machine.Pin(6), 1)
np[0] = [0, 0, 0]
np.write()

# --- Run I2C recovery on both buses BEFORE main.py creates I2C objects ---

# Extract I2C pins from board configuration
I2C0_SDA = board['pins']['i2c0_sda']
I2C0_SCL = board['pins']['i2c0_scl']
I2C1_SDA = board['pins']['i2c1_sda']
I2C1_SCL = board['pins']['i2c1_scl']

ok0 = i2c_bus_recover(I2C0_SCL, I2C0_SDA)
ok1 = i2c_bus_recover(I2C1_SCL, I2C1_SDA)

if not ok0 or not ok1:
    print("I2C recovery: ", end="")
    if not ok0:
        print("bus 0 stuck", end="")
        if not ok1:
            print(", ", end="")
    if not ok1:
        print("bus 1 stuck", end="")
    print()
else:
    print("Hardware ready")