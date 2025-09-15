# Sensor Reading Example
# This example shows how to read all the different sensors on your GBE Box
# It will continuously display sensor readings every 5 seconds

import gbebox
import time

print("Starting sensor reading example...")
print("This program will read sensors every 5 seconds. Press Ctrl+C to stop.")

# Turn on blue status LED to show program is running
gbebox.indicator.on("blue")

# Counter to track how many readings we've taken
reading_count = 0

while True:  # Run forever until stopped
    reading_count += 1
    print(f"\n--- Sensor Reading #{reading_count} ---")
    
    # Temperature reading (priority: SHT35 > MPL3115A2 > SCD4x > Seesaw)
    temp = gbebox.sensor.temperature()
    if temp is not None:  # Check if sensor gave us a valid reading
        print(f"Temperature: {temp}°C")
        # Show which sensor provided the reading
        print(f"  (from {gbebox.sensor.temperature.device} sensor)")
    else:
        print("Temperature: No sensor connected")
    
    # Humidity reading (priority: SHT35 > SCD4x)
    humidity = gbebox.sensor.humidity()
    if humidity is not None:
        print(f"Humidity: {humidity}%")
        print(f"  (from {gbebox.sensor.humidity.device} sensor)")
    else:
        print("Humidity: No sensor connected")
    
    # CO2 reading (from SCD4x sensor only)
    co2 = gbebox.sensor.co2()
    if co2 is not None:
        print(f"CO2: {co2} ppm")
        # Provide context about CO2 levels
        if co2 < 400:
            print("  (Excellent air quality)")
        elif co2 < 800:
            print("  (Good air quality)")
        elif co2 < 1200:
            print("  (Moderate air quality - consider ventilation)")
        else:
            print("  (Poor air quality - ventilation needed)")
    else:
        print("CO2: No sensor connected")
    
    # Atmospheric pressure (from MPL3115A2 sensor)
    pressure = gbebox.sensor.pressure()
    if pressure is not None:
        # Convert from Pascals to more familiar units
        pressure_hpa = pressure / 100  # Convert to hectopascals (hPa)
        print(f"Pressure: {pressure} Pa ({pressure_hpa:.1f} hPa)")
    else:
        print("Pressure: No sensor connected")
    
    # Light level (from VEML7700 sensor)
    lux = gbebox.sensor.lux()
    if lux is not None:
        print(f"Light Level: {lux} lux")
        # Provide context about light levels
        if lux < 10:
            print("  (Very dark)")
        elif lux < 100:
            print("  (Room lighting)")
        elif lux < 1000:
            print("  (Bright indoor lighting)")
        else:
            print("  (Very bright - outdoor level)")
    else:
        print("Light Level: No sensor connected")
    
    # Power monitoring (from INA219 sensor - usually always present)
    voltage = gbebox.sensor.voltage()
    current = gbebox.sensor.current()
    power = gbebox.sensor.power()
    
    if voltage is not None:
        print(f"System Voltage: {voltage} V")
    if current is not None:
        print(f"System Current: {current} mA")
    if power is not None:
        print(f"System Power: {power} W")
    
    # Fan speed monitoring
    fan_speed = gbebox.sensor.fan_speed()
    if fan_speed is not None:
        print(f"Fan Speed: {fan_speed} RPM")
    else:
        print("Fan Speed: No RPM sensor connected")
    
    # Soil moisture (if soil sensor is connected)
    moisture = gbebox.sensor.moisture()
    if moisture is not None:
        print(f"Soil Moisture: {moisture}")
    else:
        print("Soil Moisture: No soil sensor connected")
    
    # Show memory usage (useful for debugging)
    memory_info = gbebox.sensor.get_memory_usage()
    print(f"Memory - Free: {memory_info['free']} bytes, Used: {memory_info['allocated']} bytes")
    
    # Flash status LED to show we completed a reading cycle
    gbebox.indicator.on("green")
    time.sleep(0.2)  # Brief green flash
    gbebox.indicator.on("blue")
    
    # Wait 5 seconds before next reading
    print("Waiting 5 seconds for next reading...")
    time.sleep(5)