# Simple Greenhouse Control Example
# This is a beginner-friendly example that combines basic sensor reading with simple automation
# Perfect for students just starting with the GBE Box

import gbebox
import time

print("Welcome to the Simple Greenhouse Controller!")
print("This program will help you grow plants by automatically controlling light and air.")
print()

# Ask the user to set their preferences (in a real greenhouse, these might be saved to SD card)
print("=== Greenhouse Setup ===")
print("First, let's set up your greenhouse preferences...")

# For this example, we'll use simple preset values
# In a more advanced program, students could input their own values
DAYTIME_TEMP_MAX = 30.0    # Turn on fan if temperature goes above this
NIGHTTIME_TEMP_MIN = 18.0  # Turn on heater light if temperature goes below this
LIGHTS_ON_HOUR = 7         # Morning: turn lights on
LIGHTS_OFF_HOUR = 19       # Evening: turn lights off

print(f"Daytime temperature limit: {DAYTIME_TEMP_MAX}°C")
print(f"Nighttime temperature minimum: {NIGHTTIME_TEMP_MIN}°C") 
print(f"Light schedule: {LIGHTS_ON_HOUR}:00 AM to {LIGHTS_OFF_HOUR}:00 PM")
print()

# Show which sensors are available
print("=== Checking Available Sensors ===")
available_sensors = gbebox.sensor.get_available_sensors()
if available_sensors:
    print("Connected sensors:")
    for sensor in available_sensors:
        print(f"  ✓ {sensor}")
else:
    print("  No sensors detected")
print()

# Main control loop
print("=== Starting Greenhouse Control ===")
print("The greenhouse is now running! Press Ctrl+C to stop.")
print()

cycle_count = 0

try:
    while True:  # Run forever until user stops program
        cycle_count += 1
        print(f"--- Control Cycle #{cycle_count} ---")
        
        # Get current time to determine if it's day or night
        current_time = gbebox.clock.get_current_datetime()
        current_hour = current_time[3]  # Extract hour (0-23)
        current_minute = current_time[4]  # Extract minute
        
        # Determine if it's daytime or nighttime
        is_daytime = LIGHTS_ON_HOUR <= current_hour < LIGHTS_OFF_HOUR
        time_status = "DAYTIME" if is_daytime else "NIGHTTIME"
        
        print(f"Time: {current_hour:02d}:{current_minute:02d} ({time_status})")
        
        # STEP 1: Control the lights based on time of day
        if is_daytime:
            print("  → Turning lights ON for plant growth")
            # Use a good spectrum for plant growth (more red and blue)
            gbebox.light.rgbw(100, 30, 50, 60)  # Red-blue spectrum with some white
        else:
            print("  → Turning lights OFF for plant rest")
            gbebox.light.off()
        
        # STEP 2: Read temperature and control fan/heating
        temperature = gbebox.sensor.temperature()
        
        if temperature is not None:
            print(f"  Temperature: {temperature}°C")
            
            if is_daytime:
                # Daytime: prevent overheating with fan
                if temperature > DAYTIME_TEMP_MAX:
                    print(f"  → Too hot! Turning on cooling fan (>{DAYTIME_TEMP_MAX}°C)")
                    gbebox.fan.on(speed=128)  # High speed for cooling
                    gbebox.indicator.on("red")  # Red = cooling mode
                else:
                    print(f"  → Temperature OK, gentle air circulation")
                    gbebox.fan.on(speed=64)   # Low speed for air movement
                    gbebox.indicator.on("green")  # Green = all good
            else:
                # Nighttime: prevent getting too cold
                if temperature < NIGHTTIME_TEMP_MIN:
                    print(f"  → Too cold! Adding heat light (<{NIGHTTIME_TEMP_MIN}°C)")
                    # Add some warm white light for heat (even though main lights are off)
                    gbebox.light.white(80)
                    gbebox.fan.off()  # Don't blow cold air around
                    gbebox.indicator.on("blue")  # Blue = heating mode
                else:
                    print(f"  → Temperature OK for nighttime")
                    gbebox.fan.on(speed=50)  # Very low speed, just a little air movement
                    gbebox.indicator.on("green")
        else:
            print("  Temperature sensor not available")
            gbebox.indicator.on("yellow")  # Yellow = sensor problem
        
        # STEP 3: Check humidity (if available)
        humidity = gbebox.sensor.humidity()
        if humidity is not None:
            print(f"  Humidity: {humidity}%")
            if humidity < 40:
                print("    (Low humidity - plants might need water)")
            elif humidity > 80:
                print("    (High humidity - good ventilation needed)")
            else:
                print("    (Humidity level is good)")
        
        # STEP 4: Check CO2 levels (if available)
        co2 = gbebox.sensor.co2()
        if co2 is not None:
            print(f"  CO2: {co2} ppm")
            if co2 > 1000:
                print("    (CO2 high - increasing ventilation)")
                # Make sure fan is running at least medium speed
                current_fan = gbebox.fan.setting()
                if current_fan < 120:
                    gbebox.fan.on(speed=120)
            else:
                print("    (CO2 level is fine)")
        
        # STEP 5: Check light levels (if available)
        light_level = gbebox.sensor.lux()
        if light_level is not None:
            print(f"  Light Level: {light_level} lux")
            if is_daytime and light_level < 100:
                print("    (Low light detected - LED panel is providing light)")
            elif not is_daytime and light_level > 50:
                print("    (Some external light detected during rest period)")
        
        # STEP 6: Show system status
        voltage = gbebox.sensor.voltage()
        power = gbebox.sensor.power()
        if voltage is not None and power is not None:
            print(f"  System Power: {voltage}V, {power}W")
        
        # Show current settings
        fan_speed = gbebox.fan.setting()
        r, g, b, w = gbebox.light.rgbw()
        print(f"  Current Settings: Fan={fan_speed}, Lights=({r},{g},{b},{w})")
        
        print()  # Empty line for readability
        
        # Wait 2 minutes before next control cycle
        # This gives you time to observe changes and isn't too frequent
        print("Waiting 2 minutes before next check...")
        
        # Count down with LED flashes so you know it's still running
        for i in range(12):  # 12 intervals of 10 seconds = 120 seconds (2 minutes)
            time.sleep(10)
            # Brief flash to show the program is still running
            current_color = "green" if gbebox.indicator.on else "green"
            gbebox.indicator.on("white")
            time.sleep(0.1)
            gbebox.indicator.on(current_color)
        
        print()  # Extra line before next cycle

except KeyboardInterrupt:
    # This runs when user presses Ctrl+C to stop the program
    print("\n=== Greenhouse Controller Stopped ===")
    print("Shutting down safely...")
    
    # Turn everything off cleanly
    gbebox.light.off()
    gbebox.fan.off()
    gbebox.indicator.on("red")  # Red indicates system is stopped
    
    print("Lights OFF")
    print("Fan OFF") 
    print("Thank you for using the Simple Greenhouse Controller!")
    print("Your plants appreciate the care! 🌱")