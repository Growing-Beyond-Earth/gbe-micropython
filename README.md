# Growing Beyond Earth (GBE) Box Control Software

MicroPython software for the GBE Vegetable Production System control circuit, built on Raspberry Pi Pico W.

## About Growing Beyond Earth

Growing Beyond Earth® (GBE) is a citizen science project created by **Fairchild Tropical Botanic Garden** in partnership with **NASA**. GBE experiments on Earth are helping NASA learn to grow food on spacecraft, paving the way for future exploration into deep space.

## What is the GBE Box?

The GBE Vegetable Production System is a tabletop growth chamber similar to experimental gardens on the International Space Station. It can accommodate many kinds of leafy green vegetables and herbs, along with some root vegetables and fruiting crops.

### Key Features:
- **Automated plant growth environment** with programmable LED lighting and fan control
- **Environmental monitoring** via temperature, humidity, CO2, and light sensors
- **Data logging** to SD card and cloud upload via WiFi
- **Raspberry Pi Pico W microcontroller** running MicroPython
- **Student-friendly programming** for educational experiments

## Hardware Components

### Control System:
- **Raspberry Pi Pico W** microcontroller with WiFi
- **RGBW LED panel** for customizable plant lighting
- **Variable speed fan** for air circulation and cooling
- **NeoPixel status indicator** for system feedback

### Sensors (Optional):
- **SHT35/SCD4X** - Temperature and humidity
- **SCD4X** - CO2 concentration  
- **MPL3115A2** - Atmospheric pressure and temperature
- **VEML7700** - Light intensity (lux)
- **INA219** - Power monitoring (voltage, current, watts)
- **Seesaw** - Soil moisture and temperature
- **Fan RPM sensor** - Fan speed monitoring

### Storage & Connectivity:
- **SD card** for data logging and configuration
- **WiFi connectivity** for cloud data upload and time sync
- **USB** for programming and development

## Software Architecture

This software provides a unified MicroPython library (`gbebox`) that abstracts hardware control and sensor reading into simple, student-friendly functions.

### Core Modules:
- **`hardware.py`** - Board configuration and hardware interfaces (I2C, SPI, pins)
- **`sensors.py`** - Unified sensor management with automatic fallbacks
- **`actuators.py`** - LED light and fan control
- **`indicator.py`** - Status LED effects and notifications
- **`storage.py`** - SD card operations and configuration management
- **`networking.py`** - WiFi connectivity and network utilities
- **`clock.py`** - Time synchronization and scheduling

### Application Layer:
- **`application/`** - Higher-level program execution, data logging, and system management

## Quick Start

### 1. Hardware Setup
1. Assemble your GBE Box according to the hardware guide
2. Insert SD card with configuration files
3. Connect optional sensors to I2C ports
4. Power on the system

### 2. Basic Programming
```micropython
import gbebox

# Turn on soft white light
gbebox.light.on()

# Read temperature
temp = gbebox.sensor.temperature()
if temp:
    print(f"Temperature: {temp}°C")

# Control fan based on temperature
if temp and temp > 25:
    gbebox.fan.on(speed=150)  # Cooling
else:
    gbebox.fan.on(speed=80)   # Gentle circulation
```

### 3. Run Examples
Check the `examples/` folder for complete programs:
- `01_basic_lights.py` - LED control basics
- `02_read_sensors.py` - Sensor monitoring
- `03_climate_control.py` - Advanced automation
- `04_data_logging.py` - Data collection
- `05_simple_greenhouse.py` - Beginner automation

## Documentation

- **`dictionary.md`** - Complete function reference for students
- **`examples/README.md`** - Guide to example programs
- **MicroPython Docs** - https://docs.micropython.org/

## Educational Use

This software is designed for **middle and high school students** learning:
- **Environmental science** - Understanding plant growth conditions
- **Programming fundamentals** - Variables, loops, functions, conditionals
- **Data collection** - Scientific measurement and logging
- **Automation** - Sensor-based control systems
- **IoT concepts** - Connected devices and cloud data

### Safety Features:
- **Automatic LED current limiting** to prevent overheating
- **Sensor validation** with graceful error handling  
- **Hardware reset** on boot for safe operation
- **Status indicators** for system health monitoring

## System Requirements

### Hardware:
- Raspberry Pi Pico W microcontroller
- MicroSD card (8GB+ recommended)
- Power supply (5V, 3A minimum)

### Software:
- **MicroPython** firmware for Raspberry Pi Pico W
- **Thonny IDE** or similar for development
- SD card configuration files (WiFi, timezone, programs)

## Installation

1. **Flash MicroPython** to your Raspberry Pi Pico W
2. **Copy this software** to the Pico's root directory:
   - `boot.py` - Hardware initialization
   - `main.py` - Main program entry point
   - `lib/gbebox/` - Core library modules
   - `application/` - Application logic
   - `examples/` - Student example programs
3. **Configure SD card** with WiFi and timezone settings
4. **Power on** - The system starts automatically

## Configuration

### SD Card Files:
- **`wifi.json`** - Network credentials and settings
- **`timezone.json`** - Local timezone configuration  
- **`program.json`** - Custom program parameters

### Version Management:
The software version is stored in `version.txt` for easy updates.

## Development

### File Structure:
```
/
├── boot.py              # Hardware initialization
├── main.py             # Program entry point
├── version.txt         # Software version
├── board.json          # Hardware pin configuration
├── lib/                # MicroPython libraries
│   ├── gbebox/         # Core GBE Box library
│   │   ├── __init__.py     # Main API
│   │   ├── hardware.py     # Hardware abstraction
│   │   ├── sensors.py      # Sensor management
│   │   ├── actuators.py    # Light/fan control
│   │   ├── indicator.py    # Status LED
│   │   ├── storage.py      # SD card operations
│   │   ├── networking.py   # WiFi management
│   │   └── clock.py        # Time utilities
│   ├── application/    # Application logic
│   │   ├── __init__.py     # Application modules
│   │   ├── logic.py        # Program execution logic
│   │   └── utils.py        # Utility functions
│   ├── drivers/        # Hardware driver libraries
│   │   ├── scd4x.py        # CO2 sensor driver
│   │   ├── ina219_gbe.py   # Power monitor driver
│   │   ├── veml7700.py     # Light sensor driver
│   │   └── ...             # Other sensor drivers
│   └── json_utils/     # JSON utilities
│       ├── jpretty.py      # Pretty JSON formatting
│       └── jsum.py         # JSON summary functions
├── examples/           # Student example programs
├── defaults/          # Default configuration files
└── cache/            # Runtime cache directory
```

### Contributing:
1. Follow MicroPython best practices
2. Add comprehensive inline comments for students
3. Test on actual hardware before committing
4. Update documentation for any API changes

## Support

- **Project Website**: https://www.fairchildgarden.org/gbe
- **Educational Resources**: See `dictionary.md` and `examples/`
- **MicroPython Help**: https://docs.micropython.org/

## License

This software is developed by **Fairchild Tropical Botanic Garden** in partnership with **NASA** for the Growing Beyond Earth® educational program.

---

**Growing Beyond Earth® - Growing the future of space exploration, one plant at a time.**