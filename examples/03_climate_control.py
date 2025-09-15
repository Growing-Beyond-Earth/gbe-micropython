# Automated Climate Control Example
# This example shows how to automatically control lights and fan based on sensor readings
# This is an asynchronous program that can do multiple things at the same time

import gbebox
import uasyncio as asyncio  # For running multiple tasks at once

print("Starting automated climate control example...")
print("This program will monitor temperature and automatically adjust fan and lights.")
print("Press Ctrl+C to stop the program.")

# Set your desired temperature range (in Celsius)
TARGET_TEMP_MIN = 22.0  # Turn on warming lights below this temperature
TARGET_TEMP_MAX = 26.0  # Turn on cooling fan above this temperature

# Set your desired light schedule (24-hour format)
LIGHTS_ON_HOUR = 8   # Turn lights on at 8 AM
LIGHTS_OFF_HOUR = 20 # Turn lights off at 8 PM

async def monitor_temperature():
    """This function runs continuously to monitor and control temperature"""
    while True:
        # Read current temperature
        temp = gbebox.sensor.temperature()
        
        if temp is not None:  # Make sure we got a valid reading
            print(f"Current temperature: {temp}°C (Target range: {TARGET_TEMP_MIN}-{TARGET_TEMP_MAX}°C)")
            
            # Temperature control logic
            if temp > TARGET_TEMP_MAX:
                # Too hot - turn on fan for cooling
                print(f"  Temperature too high! Turning on fan...")
                gbebox.fan.on(speed=180)  # High speed cooling
                gbebox.indicator.on("red")  # Red light indicates cooling mode
                
            elif temp < TARGET_TEMP_MIN:
                # Too cold - turn off fan and increase lights for warmth
                print(f"  Temperature too low! Increasing lights for warmth...")
                gbebox.fan.off()
                # Add some white light for warmth (but respect the light schedule)
                current_hour = gbebox.clock.now()[3]  # Get current hour
                if LIGHTS_ON_HOUR <= current_hour < LIGHTS_OFF_HOUR:
                    gbebox.light.white(100)  # Add warm white light
                gbebox.indicator.on("blue")  # Blue light indicates heating mode
                
            else:
                # Temperature is just right
                print(f"  Temperature is perfect!")
                gbebox.fan.on(speed=80)  # Low speed for air circulation
                gbebox.indicator.on("green")  # Green light indicates optimal conditions
        
        else:
            print("  Cannot read temperature sensor")
            gbebox.indicator.on("yellow")  # Yellow indicates sensor problem
        
        # Wait 30 seconds before checking temperature again
        await asyncio.sleep(30)

async def control_light_schedule():
    """This function controls the daily light schedule"""
    while True:
        # Get current time
        current_time = gbebox.clock.now()
        current_hour = current_time[3]  # Hour (0-23)
        current_minute = current_time[4]  # Minute (0-59)
        
        print(f"Current time: {current_hour:02d}:{current_minute:02d}")
        
        # Check if lights should be on or off based on schedule
        if LIGHTS_ON_HOUR <= current_hour < LIGHTS_OFF_HOUR:
            # Lights should be on - set to growing light spectrum
            print(f"  Lights ON (scheduled {LIGHTS_ON_HOUR}:00 - {LIGHTS_OFF_HOUR}:00)")
            # Use a spectrum good for plant growth (more red and blue)
            gbebox.light.rgbw(120, 40, 60, 80)  # Red-heavy spectrum for growth
            
        else:
            # Lights should be off for plant rest period
            print(f"  Lights OFF (scheduled {LIGHTS_OFF_HOUR}:00 - {LIGHTS_ON_HOUR}:00)")
            gbebox.light.off()
        
        # Check light schedule every 10 minutes
        await asyncio.sleep(600)

async def monitor_air_quality():
    """This function monitors CO2 levels and provides ventilation control"""
    while True:
        co2 = gbebox.sensor.co2()
        
        if co2 is not None:
            print(f"CO2 level: {co2} ppm")
            
            if co2 > 1000:
                # High CO2 - increase ventilation
                print(f"  CO2 too high! Increasing ventilation...")
                # Make sure fan is running at least at medium speed
                current_fan_speed = gbebox.fan.setting()
                if current_fan_speed < 120:
                    gbebox.fan.on(speed=120)
                    
            elif co2 > 800:
                print(f"  CO2 slightly elevated - monitoring...")
                
            else:
                print(f"  CO2 levels are good")
        
        else:
            print("  Cannot read CO2 sensor")
        
        # Check CO2 every 5 minutes
        await asyncio.sleep(300)

async def log_data():
    """This function logs sensor data every 15 minutes"""
    while True:
        print("\n--- Data Log Entry ---")
        
        # Get all sensor readings
        all_sensors = gbebox.sensor.all
        
        # Print timestamp
        current_time = gbebox.clock.now()
        timestamp = f"{current_time[0]}-{current_time[1]:02d}-{current_time[2]:02d} {current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"
        print(f"Time: {timestamp}")
        
        # Print all sensor values
        for sensor_name, value in all_sensors.items():
            if value is not None:
                print(f"{sensor_name}: {value}")
        
        # Also log current fan and light settings
        fan_speed = gbebox.fan.setting()
        r, g, b, w = gbebox.light.rgbw()
        print(f"Fan Speed: {fan_speed}")
        print(f"Light RGBW: {r}, {g}, {b}, {w}")
        print("--- End Log Entry ---\n")
        
        # Log every 15 minutes
        await asyncio.sleep(900)

async def main():
    """Main function that starts all the control tasks"""
    print("Starting all climate control tasks...")
    
    # Start all tasks at the same time (asynchronous programming!)
    # Each task runs independently but can share resources
    tasks = [
        asyncio.create_task(monitor_temperature()),
        asyncio.create_task(control_light_schedule()),
        asyncio.create_task(monitor_air_quality()),
        asyncio.create_task(log_data())
    ]
    
    # Run all tasks forever
    await asyncio.gather(*tasks)

# Start the main program
# This runs all the async functions at the same time
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nProgram stopped by user")
    # Clean shutdown
    gbebox.light.off()
    gbebox.fan.off()
    gbebox.indicator.off()
    print("All systems turned off. Goodbye!")