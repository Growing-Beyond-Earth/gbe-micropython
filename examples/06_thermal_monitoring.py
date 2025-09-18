# Environmental Temperature Monitoring Example
# This example demonstrates how to monitor environmental temperature
# sensors on the GBE Box

import gbebox
import time

print("Starting environmental temperature monitoring...")
print("This program monitors environmental temperature sensors available on the GBE Box.")
print()

# Turn on blue status LED to show program is running
gbebox.indicator.on("blue")

# Check for environmental temperature sensors
env_temp_available = False
try:
    env_temp = gbebox.sensor.temperature()
    if env_temp is not None:
        print(f"✓ Environmental temperature sensor available: {env_temp}°C")
        env_temp_available = True
    else:
        print("✗ Environmental temperature sensor not available")
except Exception as e:
    print(f"✗ Error accessing environmental temperature sensor: {e}")

if not env_temp_available:
    print("No temperature sensors available. Exiting.")
    exit()

print()
print("=== Temperature Monitoring ===")
print("• Environmental temperature: External sensor for environmental monitoring")
print("• Monitoring helps optimize growing conditions and system performance")
print()

# Monitor temperature readings
reading_count = 0

while True:  # Run forever until stopped
    reading_count += 1
    
    print(f"--- Temperature Reading #{reading_count} ---")
    
    # Read environmental temperature
    env_temp = gbebox.sensor.temperature()
    if env_temp is not None:
        print(f"Environmental Temperature: {env_temp}°C")
        
        # Provide temperature guidance for growing
        if env_temp > 30:
            print("   🔥 High temperature - consider cooling")
            gbebox.indicator.on("red")
        elif env_temp > 25:
            print("   ☀️  Warm temperature - good for most plants")
            gbebox.indicator.on("yellow")
        elif env_temp > 18:
            print("   🌡️  Moderate temperature - suitable for many plants")
            gbebox.indicator.on("green")
        else:
            print("   ❄️  Cool temperature - may need heating")
            gbebox.indicator.on("cyan")
    
    # Show other environmental sensors for context
    humidity = gbebox.sensor.humidity()
    if humidity is not None:
        print(f"Humidity: {humidity}%")
    
    co2 = gbebox.sensor.co2()
    if co2 is not None:
        print(f"CO2: {co2} ppm")
    
    # Show system info for context
    voltage = gbebox.sensor.voltage()
    power = gbebox.sensor.power()
    if voltage and power:
        print(f"System Power: {voltage:.1f}V, {power:.1f}W")
    
    fan_speed = gbebox.fan.setting()
    fan_rpm = gbebox.sensor.fan_speed()
    if fan_rpm:
        print(f"Fan: {fan_speed}/255 setting, {fan_rpm} RPM actual")
    else:
        print(f"Fan: {fan_speed}/255 setting")
    
    print()
    print("Waiting 10 seconds for next reading...")
    print("(Press Ctrl+C to stop)")
    
    # Wait with brief activity indicator
    for i in range(10):
        time.sleep(1)
        
        # Brief flash every 2 seconds to show activity
        if i % 2 == 0:
            gbebox.indicator.on("white")
            time.sleep(0.1)
            gbebox.indicator.on("blue")

print("Temperature monitoring stopped.")