#  This is a minimal Micropyton script for running the Growing Beyond
#  Earth(R) Control Box. It turns the fan on to its default setting,
#  and repeats 12-hour on/off cycles with lights at their default
#  settings. This script has no interaction with sensors and no data
#  logging.

import time
import gbebox          # load the GBE Control Box library

gbebox.fan.on()        # turn the fan on to its default setting

while True:            # repeat forever
    gbebox.light.on()  # turn the lights on to their default settings
    time.sleep(43200)  # wait 12 hours
    gbebox.light.off() # turn the lights off
    time.sleep(43200)  # wait 12 hours
