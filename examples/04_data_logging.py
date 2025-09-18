# Data Logging Example
# This example shows how to collect and save sensor data to the SD card
# It creates CSV files that can be opened in Excel or Google Sheets

import gbebox
import time

print("Starting data logging example...")
print("This program will save sensor data to the SD card every minute.")

# Check if SD card is available
if not gbebox.sd.is_present():
    print("ERROR: No SD card detected! Please insert an SD card and restart.")
    gbebox.indicator.on("red")
    exit()

if not gbebox.sd.is_mounted():
    if gbebox.sd.mount():
        print("SD card mounted successfully")
    else:
        print("ERROR: Could not mount SD card!")
        gbebox.indicator.on("red")
        exit()

# Create filename with current date
current_time = gbebox.clock.get_current_datetime()
date_string = f"{current_time[0]}-{current_time[1]:02d}-{current_time[2]:02d}"
filename = f"sensor_data_{date_string}.csv"

print(f"Data will be saved to: {filename}")

# Create CSV header (column names) if file doesn't exist
try:
    # Try to read the file to see if it already exists
    existing_data = gbebox.sd.read_file(filename)
    if not existing_data:
        # File doesn't exist, create header
        header = "Timestamp,Temperature_C,Humidity_%,CO2_ppm,Pressure_Pa,Light_lux,Voltage_V,Current_mA,Power_W,Fan_RPM,Fan_Setting\n"
        gbebox.sd.write_file(filename, header)
        print("Created new CSV file with header")
    else:
        print("Appending to existing CSV file")
except:
    # If there's any error, create new file with header
    header = "Timestamp,Temperature_C,Humidity_%,CO2_ppm,Pressure_Pa,Light_lux,Voltage_V,Current_mA,Power_W,Fan_RPM,Fan_Setting\n"
    gbebox.sd.write_file(filename, header)
    print("Created new CSV file with header")

# Turn on green status LED to show logging is active
gbebox.indicator.on("green")

# Counter for log entries
log_count = 0

while True:  # Run forever until stopped
    log_count += 1
    print(f"\n--- Recording Data Entry #{log_count} ---")
    
    # Get current timestamp
    current_time = gbebox.clock.get_current_datetime()
    timestamp = f"{current_time[0]}-{current_time[1]:02d}-{current_time[2]:02d} {current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"
    
    # Read all sensors
    temp = gbebox.sensor.temperature()
    humidity = gbebox.sensor.humidity()
    co2 = gbebox.sensor.co2()
    pressure = gbebox.sensor.pressure()
    lux = gbebox.sensor.lux()
    voltage = gbebox.sensor.voltage()
    current = gbebox.sensor.current()
    power = gbebox.sensor.power()
    fan_rpm = gbebox.sensor.fan_speed()
    fan_setting = gbebox.fan.setting()
    
    # Create CSV row (replace None values with empty string)
    def format_value(value):
        """Convert sensor reading to CSV format"""
        if value is None:
            return ""  # Empty cell for missing data
        else:
            return str(value)
    
    csv_row = f"{timestamp},{format_value(temp)},{format_value(humidity)},{format_value(co2)},{format_value(pressure)},{format_value(lux)},{format_value(voltage)},{format_value(current)},{format_value(power)},{format_value(fan_rpm)},{format_value(fan_setting)}\n"
    
    # Display what we're saving
    print(f"Time: {timestamp}")
    if temp is not None:
        print(f"Temperature: {temp}°C")
    if humidity is not None:
        print(f"Humidity: {humidity}%")
    if co2 is not None:
        print(f"CO2: {co2} ppm")
    if pressure is not None:
        print(f"Pressure: {pressure} Pa")
    if lux is not None:
        print(f"Light: {lux} lux")
    if voltage is not None:
        print(f"System: {voltage}V, {current}mA, {power}W")
    if fan_rpm is not None:
        print(f"Fan: {fan_rpm} RPM (setting: {fan_setting})")
    
    # Try to save data to SD card
    try:
        # Read existing file content
        existing_data = gbebox.sd.read_file(filename)
        if existing_data is None:
            existing_data = ""
        
        # Append new row
        new_data = existing_data + csv_row
        
        # Write back to file
        success = gbebox.sd.write_file(filename, new_data)
        
        if success:
            print(f"✓ Data saved to {filename}")
            # Brief blue flash to show successful save
            gbebox.indicator.on("blue")
            time.sleep(0.2)
            gbebox.indicator.on("green")
        else:
            print("✗ Failed to save data to SD card")
            gbebox.indicator.on("red")
            time.sleep(1)
            gbebox.indicator.on("green")
            
    except Exception as e:
        print(f"✗ Error saving data: {e}")
        gbebox.indicator.on("red")
        time.sleep(1)
        gbebox.indicator.on("green")
    
    # Show memory usage (important for long-running data logging)
    memory_info = gbebox.sensor.get_memory_usage()
    print(f"Memory: {memory_info['free']} bytes free")
    
    # Wait 1 minute before next reading
    print("Waiting 60 seconds for next data point...")
    
    # Count down with status LED flashes every 10 seconds
    for i in range(6):  # 6 intervals of 10 seconds = 60 seconds
        time.sleep(10)
        # Quick flash to show we're still running
        gbebox.indicator.on("yellow")
        time.sleep(0.1)
        gbebox.indicator.on("green")
        
        # Show countdown
        remaining = 50 - (i * 10)
        if remaining > 0:
            print(f"  {remaining} seconds remaining...")

print("Data logging stopped.")