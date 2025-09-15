#   GROWING BEYOND EARTH SOFTWARE
# RASPBERRY PI PICO W / MICROPYTHON

# FAIRCHILD TROPICAL BOTANIC GARDEN

# The Growing Beyond Earth (GBE) control box is a device that controls
# the LED lights and fan in a GBE growth chamber. It can also control
# accessories including a 12v water pump and environmental sensors.
# The device is based on a Raspberry Pi Pico W microcontroller running
# MicroPython.

# This program (main.py) runs automatically each time the device is
# powered up.

import time
import sys
import gbebox
import json
from json_utils import jpretty
import uasyncio as asyncio
from io import StringIO
from machine import bootloader


# Function to determine whether main.py was run from the REPL (e.g. Thonny)
# or automatically at startup
def run_from_repl():
    try: 
        raise ZeroDivisionError  # Intentionally raise an exception
    except ZeroDivisionError as e:
        s = StringIO()  # Create a StringIO object to capture the exception output
        sys.print_exception(e, s)  # Print the exception traceback to the StringIO object
        return "<stdin>" in s.getvalue()  # Check if "<stdin>" is in the captured output
    




async def main():
    
    print("  ____ ____  _____")
    print(" / ___| __ )| ____|   GROWING BEYOND EARTH(R)")
    print("| |  _|  _ \\|  _|     FAIRCHILD TROPICAL BOTANIC GARDEN")
    print("| |_| | |_) | |___    Raspberry Pi Pico W / MicroPython")
    print(" \\____|____/|_____|   Software release date: " + gbebox.software_date + "\n\n")


    # Attempt to load previous run data from JSON, set lastrun to False if unavailable
    try:
        with open('/cache/lastrun.json', 'r') as lr_file:
            lastrun = json.load(lr_file)
    except:
        lastrun = False  # Default to False if file read fails

    # Gather current run information
    thisrun = {
        "status": {
            "timestamp": time.time(),
            "run_from_repl": str(run_from_repl()).lower(),
            "usb_connected": str(gbebox.usb_connected()).lower(),
            "power_connected": str(gbebox.sensor.voltage() > 0).lower(),
            "launched_bootloader": "false"
        }
    }

    # Check conditions to determine if bootloader should be launched
    if lastrun and all([
        lastrun["status"]["launched_bootloader"] == "false",
        lastrun["status"]["usb_connected"] == "true",
        thisrun["status"]["usb_connected"] == "true",
        thisrun["status"]["power_connected"] == "false",
        thisrun["status"]["run_from_repl"] == "false"
    ]):
        thisrun["status"]["launched_bootloader"] = "true"

    # Save current run data to JSON, including updated bootloader status
    with open('/cache/lastrun.json', 'w') as lr_file:
        lr_file.write(jpretty.jpretty(thisrun))

    # Launch bootloader if required and indicate with green light
    if thisrun["status"]["launched_bootloader"] == "true":
        gbebox.indicator.on("green")
        bootloader() 

    # Startup pulse
    await gbebox.indicator.pulse(color="magenta", duration=1)
    
    # Connect to Wi-Fi
    gbebox.wifi.connect()

    # Print hardware info
    gbebox.system.display_system_info()
   

    # Create an instance of the Run class with a custom logging interval (e.g., 600 seconds)
    log_interval = 600  # Set the logging interval here
    sensor_check_interval = 300  # Set the sensor check interval here
    run_instance = gbebox.Run(log_interval=log_interval, sensor_check_interval=sensor_check_interval)  # Pass the log interval to the Run instance

    # Start necessary tasks
    asyncio.create_task(gbebox.clock.setdaily())
    asyncio.create_task(gbebox.indicator.status())
    asyncio.create_task(gbebox.wifi.check_connection())  # Reconnect wifi if it drops
    asyncio.create_task(run_instance.logger.start_logging())  # Start the logger, saving to sd card and the cloud
    asyncio.create_task(run_instance.gc.start())  # Start garbage collection, reclaim unused memory every 5 seconds
    asyncio.create_task(gbebox.sensor.monitor_sensor_changes())  # Monitor for hot-plugged sensors 
    
    if gbebox.usb_connected() is False:
        asyncio.create_task(run_instance.watchdog.start())  # Start the watchdog, restart the system if it freezes
    
    asyncio.create_task(run_instance.program())  # Start the main program execution

    print("\n" + "Program running" + "\n")

# Start the event loop
loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()