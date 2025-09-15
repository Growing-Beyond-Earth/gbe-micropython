# GBE Box MicroPython Programming Reference

This document provides a comprehensive reference for all commands and functions available when programming the GBE Box hardware using MicroPython. This guide is designed for middle and high school students learning to control environmental chambers and sensors.

## Getting Started

Before you can control any hardware, you need to import the GBE Box library at the top of your program:

```micropython
import gbebox
```

This single import statement gives you access to all the sensors, lights, fans, and other hardware connected to your GBE Box.

---

## Hardware Control

### LED Lights

The GBE Box has an RGBW (Red, Green, Blue, White) LED panel that provides light for plant growth. You can control each color channel individually or all together. Think of it like mixing paint colors - you combine different amounts of red, green, blue, and white to create any color you want.

```micropython
# Turn lights on with default settings (soft white)
gbebox.light.on()

# Turn lights on with custom RGBW values
gbebox.light.on(r=50, g=10, b=20, w=100)

# Turn all lights off
gbebox.light.off()

# Set individual color channels (0-255 scale, but each has a safety limit)
# The GBE Box automatically limits each channel to prevent LED overheating
gbebox.light.red(25)      # Red: 0-160 (values above 160 are set to 160)
gbebox.light.green(15)    # Green: 0-71 (values above 71 are set to 71)
gbebox.light.blue(30)     # Blue: 0-75 (values above 75 are set to 75)
gbebox.light.white(92)    # White: 0-117 (values above 117 are set to 117)

# Get current color values
current_red = gbebox.light.red()
current_green = gbebox.light.green()
current_blue = gbebox.light.blue()
current_white = gbebox.light.white()

# Set all RGBW channels at once
gbebox.light.rgbw(25, 15, 30, 92)

# Get all current RGBW values
r, g, b, w = gbebox.light.rgbw()
```

### Fan Control

The GBE Box has a variable-speed exhaust fan that helps circulate air and control temperature. You can turn it on, off, or set it to any speed between 0 (off) and 255 (maximum speed).

```micropython
# Turn fan on with default speed
gbebox.fan.on()

# Turn fan on with specific speed (0-255)
gbebox.fan.on(speed=150)

# Turn fan off
gbebox.fan.off()

# Set fan speed directly
gbebox.fan.setting(120)

# Get current fan speed
current_speed = gbebox.fan.setting()
# or
current_speed = gbebox.fan.speed
```

### Status LED

The status LED is a small NeoPixel light that shows the current state of your GBE Box. You can use different colors to indicate different conditions in your program (like green for "everything is fine" or red for "temperature too high").

```micropython
# Turn on with specific color
gbebox.indicator.on("red")      # Available: red, green, blue, yellow, cyan, magenta, white
gbebox.indicator.on("green")
gbebox.indicator.on("blue")

# Turn off
gbebox.indicator.off()

# Pulse effect (async function - use with await)
await gbebox.indicator.pulse("magenta", duration=2)

# Solid color for duration (async)
await gbebox.indicator.solid("yellow", duration=5)

# Continuous blinking (async)
await gbebox.indicator.blink("red", interval=1)
```

---

## Sensor Readings

All sensor readings return `None` if the sensor is not connected or fails to read. This means you should always check if a sensor reading is valid before using it in your program.

### Temperature & Humidity

The GBE Box can connect to several different temperature and humidity sensors. The system automatically picks the most accurate sensor available and gives you the reading.

```micropython
# Temperature in Celsius (priority: SHT35 > MPL3115A2 > SCD4x > Seesaw)
temp = gbebox.sensor.temperature()
print(f"Temperature: {temp}°C")

# Humidity percentage (priority: SHT35 > SCD4x)
humidity = gbebox.sensor.humidity()
print(f"Humidity: {humidity}%")
```

### Air Quality

Air quality sensors measure things like CO2 (carbon dioxide) levels and atmospheric pressure. These are important for understanding the environment your plants are growing in.

```micropython
# CO2 concentration in parts per million
co2 = gbebox.sensor.co2()
print(f"CO2: {co2} ppm")

# Atmospheric pressure in Pascals
pressure = gbebox.sensor.pressure()
print(f"Pressure: {pressure} Pa")
```

### Light Level

The light sensor measures how bright the environment is in "lux" units. This helps you know if your plants are getting enough light.

```micropython
# Light intensity in lux
lux = gbebox.sensor.lux()
print(f"Light level: {lux} lx")
```

### Power Monitoring

These sensors tell you how much electrical power your GBE Box is using. This is useful for understanding energy consumption and detecting problems.

```micropython
# Voltage in volts
voltage = gbebox.sensor.voltage()
print(f"Voltage: {voltage} V")

# Current in milliamps
current = gbebox.sensor.current()
print(f"Current: {current} mA")

# Power in watts
power = gbebox.sensor.power()
print(f"Power: {power} W")
```

### System Monitoring

These sensors help you monitor the performance of your GBE Box hardware, like how fast the fan is spinning or soil moisture levels.

```micropython
# Fan speed in RPM
fan_rpm = gbebox.sensor.fan_speed()
print(f"Fan speed: {fan_rpm} RPM")

# Soil moisture (if connected)
moisture = gbebox.sensor.moisture()
print(f"Soil moisture: {moisture}")
```

### All Sensors at Once

Sometimes you want to read all sensors at the same time. This function returns a dictionary (like a list with labels) containing all available sensor readings.

```micropython
# Get all sensor readings as a dictionary
all_data = gbebox.sensor.all
print(all_data)
# Returns: {'Temperature (C)': 24.5, 'Humidity (%)': 65.2, 'CO2 (ppm)': 456, ...}
```

---

## Networking

### WiFi Connection

The GBE Box can connect to WiFi networks to upload data to the cloud and sync its clock. The WiFi settings are stored on the SD card.

```micropython
# Connect to WiFi (uses settings from SD card)
result = gbebox.wifi.connect()
print(result)  # "Connected to WiFi" or error message

# Check connection status
if gbebox.wifi.is_connected():
    print("WiFi is connected")

# Get IP address
ip = gbebox.wifi.ip_address
print(f"IP Address: {ip}")

# Disconnect from WiFi
gbebox.wifi.disconnect()
```

### Network Information

These functions help you check the status of your network connection and get information about your GBE Box's network settings.

```micropython
# Get network interface configuration
config = gbebox.wifi.ifconfig
if config:
    ip, subnet, gateway, dns = config
    print(f"IP: {ip}, Gateway: {gateway}")

# Check WiFi status (for backward compatibility)
if gbebox.wlan.isconnected():
    print("Connected via wlan interface")
```

---

## Storage

### SD Card Operations

The GBE Box uses an SD card to store data, programs, and configuration files. These functions help you work with files on the SD card.

```micropython
# Check if SD card is present
if gbebox.sd.is_present():
    print("SD card detected")

# Check if SD card is mounted
if gbebox.sd.is_mounted():
    print("SD card is mounted")

# Mount the SD card
if gbebox.sd.mount():
    print("SD card mounted successfully")

# Read a file from SD card
content = gbebox.sd.read_file("data.txt")
if content:
    print(content)

# Write a file to SD card
success = gbebox.sd.write_file("log.txt", "Hello World")
if success:
    print("File written successfully")

# List files on SD card
files = gbebox.sd.list_files()
print(f"Files: {files}")
```

### Configuration Access

Configuration files on the SD card store important settings like WiFi passwords, timezone, and program parameters. You can read these settings in your programs.

```micropython
# Get WiFi configuration
wifi_config = gbebox.sd.wifi_file
if wifi_config:
    network_name = wifi_config.get("NETWORK_NAME")
    print(f"Network: {network_name}")

# Get timezone configuration
tz_config = gbebox.sd.tz_file
if tz_config:
    timezone = tz_config.get("timezone")
    print(f"Timezone: {timezone}")

# Get program configuration
program = gbebox.sd.program_json
if program:
    print("Program loaded from SD card")
```

---

## Time & Clock

### Current Time

The GBE Box keeps track of the current time and can sync with internet time servers. Time is useful for creating schedules and logging data.

```micropython
# Get current local time as tuple (year, month, day, hour, minute, second, weekday, yearday)
local_time = gbebox.clock.now()
year, month, day, hour, minute, second = local_time[:6]
print(f"Current time: {hour:02d}:{minute:02d}:{second:02d}")

# Get current date as string (YYYY-MM-DD)
current_date = gbebox.calc.current_date()
print(f"Today's date: {current_date}")
```

### Time Utilities

These helper functions make it easier to work with time in your programs. You can convert between different time formats and check if the current time falls within a specific range.

```micropython
# Convert time string to seconds
seconds = gbebox.calc.to_seconds("2:30:00")  # Returns 9000
seconds = gbebox.calc.to_seconds("1.5")      # 1.5 hours = 5400 seconds

# Check if current time is within a range
if gbebox.calc.time_within_range("09:00", "17:00"):
    print("It's during business hours")

# Check if date is within range
if gbebox.calc.date_within_range("2024-01-15", "2024-01-01", "2024-01-31"):
    print("Date is in January 2024")

# Calculate end date from start date and duration
end_date = gbebox.calc.compute_end_date("2024-01-01", 30)  # 30 days later
print(f"End date: {end_date}")
```

---

## System Information

### Hardware Info

These functions help you get information about your GBE Box hardware, like its unique ID number and what sensors are connected.

```micropython
# Display system information
gbebox.system.display_system_info()
# Shows: Hardware ID, MAC address, IP address, available sensors

# Get board information
hardware_id = gbebox.board["id"]
mac_address = gbebox.board["mac"]
print(f"Hardware ID: {hardware_id}")
print(f"MAC: {mac_address}")

# Check USB connection
if gbebox.usb_connected():
    print("USB cable is connected")

# Get software version
print(f"Software date: {gbebox.software_date}")
```

### Available Sensors

These functions show you which sensors are currently connected and working, plus information about how much memory your programs are using.

```micropython
# List all connected sensors
sensors = gbebox.sensor.get_available_sensors()
for sensor_info in sensors:
    print(sensor_info)

# Get memory usage information
memory_info = gbebox.sensor.get_memory_usage()
print(f"Free memory: {memory_info['free']} bytes")
print(f"Allocated memory: {memory_info['allocated']} bytes")
```

---

## Asynchronous Programming

### Program Execution

Asynchronous programming allows your GBE Box to do multiple things at the same time, like reading sensors while also controlling lights. Think of it like being able to walk and chew gum at the same time.

```micropython
import uasyncio as asyncio

# Create program engine for automated control
program = gbebox.ProgramEngine()

# Main execution loop
async def main():
    # Start system tasks
    asyncio.create_task(gbebox.clock.setdaily())           # Daily clock sync
    asyncio.create_task(gbebox.indicator.status())         # Status LED
    asyncio.create_task(gbebox.wifi.check_connection())     # WiFi monitoring
    
    # Create and start program instance
    run_instance = gbebox.Run()
    asyncio.create_task(run_instance.logger.start_logging()) # Data logging
    asyncio.create_task(run_instance.gc.start())             # Memory management
    asyncio.create_task(run_instance.program())              # Program execution
    
    # Your custom code here
    while True:
        temp = gbebox.sensor.temperature()
        if temp and temp > 30:
            gbebox.fan.on(200)  # High speed cooling
        elif temp and temp > 25:
            gbebox.fan.on(100)  # Low speed cooling
        else:
            gbebox.fan.off()
        
        await asyncio.sleep(60)  # Check every minute

# Run the program
asyncio.run(main())
```

### Utility Functions

These are advanced functions for managing your GBE Box system. Most students won't need these, but they're available for special situations.

```micropython
# Clean up all hardware resources (advanced use)
gbebox.cleanup_all()

# Get comprehensive system information
system_info = gbebox.get_system_info()
print(system_info)
```

---

## Quick Reference Examples

### Simple Light Control
This example shows how to create a sunrise simulation by gradually increasing the light brightness.

```micropython
import gbebox

# Sunrise simulation
for brightness in range(0, 100, 5):
    gbebox.light.rgbw(brightness//4, brightness//6, 0, brightness)
    gbebox.time.sleep(1)
```

### Environmental Monitoring
This example shows how to continuously monitor temperature, humidity, and CO2 levels.

```micropython
import gbebox

while True:
    temp = gbebox.sensor.temperature()
    humidity = gbebox.sensor.humidity()
    co2 = gbebox.sensor.co2()
    
    if temp: print(f"Temperature: {temp}°C")
    if humidity: print(f"Humidity: {humidity}%")
    if co2: print(f"CO2: {co2} ppm")
    
    gbebox.time.sleep(10)
```

### Automated Climate Control
This example shows how to automatically control your environment based on temperature readings.

```micropython
import gbebox
import uasyncio as asyncio

async def climate_control():
    while True:
        temp = gbebox.sensor.temperature()
        if temp and temp > 28:
            gbebox.fan.on(150)
            gbebox.indicator.on("red")
        elif temp and temp < 20:
            gbebox.fan.off()
            gbebox.light.white(100)  # Warming light
            gbebox.indicator.on("blue")
        else:
            gbebox.indicator.on("green")
        
        await asyncio.sleep(30)

asyncio.run(climate_control())
```

---

## 📖 Notes

- **Sensor values return `None`** if the sensor is not connected or reading fails
- **RGBW values have safety limits**: Red (0-160), Green (0-71), Blue (0-75), White (0-117). Values above these limits are automatically reduced to prevent overheating.
- **Fan speed range**: 0-255 (0 = off, 255 = maximum speed)
- **All async functions** must be used with `await` inside async functions
- **Time functions** use 24-hour format (HH:MM:SS)
- **Dates** use ISO format (YYYY-MM-DD)

## Example Programs

The `examples/` folder contains sample MicroPython programs to help you get started:

- **01_basic_lights.py** - Learn to control the LED panel with different colors and effects
- **02_read_sensors.py** - Read and display all available sensor data
- **03_climate_control.py** - Advanced automated control using asynchronous programming
- **04_data_logging.py** - Save sensor data to CSV files on the SD card  
- **05_simple_greenhouse.py** - Beginner-friendly greenhouse automation

Each example includes detailed comments explaining how the code works. Start with the basic examples and work your way up to more advanced programs.

## Additional Resources

For more information about MicroPython programming:

- **Official MicroPython Documentation**: https://docs.micropython.org/
- **MicroPython for Raspberry Pi Pico**: https://docs.micropython.org/en/latest/rp2/quickref.html
- **MicroPython Tutorial**: https://docs.micropython.org/en/latest/tutorial/index.html

These resources will help you learn more about the MicroPython language beyond the GBE Box specific functions.