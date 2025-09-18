# GBE Box Example Programs

This folder contains example MicroPython programs to help you learn how to use your GBE Box. Each example focuses on different aspects of controlling your environmental chamber.

## How to Use These Examples

1. **Copy** the example file you want to use
2. **Paste** it into Thonny or your MicroPython editor
3. **Run** the program on your GBE Box
4. **Modify** the code to experiment and learn

## Example Programs

### 01_basic_lights.py
**What it does:** Controls the RGBW LED panel with different colors and effects  
**Good for:** Learning how to control lights and understanding RGB color mixing  
**Concepts:** Basic programming, color theory, hardware control

### 02_read_sensors.py
**What it does:** Continuously reads and displays all connected sensors  
**Good for:** Understanding what sensors are available and how to read them  
**Concepts:** Sensor reading, data validation, while loops

### 03_climate_control.py
**What it does:** Advanced automated control system using asynchronous programming  
**Good for:** Advanced students who want to run multiple tasks simultaneously  
**Concepts:** Asynchronous programming, automated control systems, scheduling

### 04_data_logging.py
**What it does:** Saves sensor data to CSV files on the SD card  
**Good for:** Scientific experiments and long-term data collection  
**Concepts:** File operations, CSV format, data logging, error handling

### 05_simple_greenhouse.py
**What it does:** Beginner-friendly greenhouse controller with basic automation  
**Good for:** First automation project, combining sensors with control  
**Concepts:** Basic automation, conditional logic, time-based control

### 06_thermal_monitoring.py
**What it does:** Demonstrates thermal protection and core temperature monitoring  
**Good for:** Understanding hardware safety features and system monitoring  
**Concepts:** Hardware protection, thermal management, system monitoring

## Learning Path

**Beginner:** Start with `01_basic_lights.py`, then `02_read_sensors.py`, then `05_simple_greenhouse.py`

**Intermediate:** Try `04_data_logging.py` and modify `05_simple_greenhouse.py` with your own ideas

**Advanced:** Study `03_climate_control.py` to learn asynchronous programming, and `06_thermal_monitoring.py` for system monitoring

## Tips for Students

- **Start simple:** Begin with the basic examples and work your way up
- **Experiment:** Change the numbers in the code to see what happens
- **Read the comments:** The `#` comments explain what each line does
- **Ask questions:** If something doesn't work, ask your teacher or check the documentation
- **Be patient:** Learning programming takes practice!

## Safety Notes

- The GBE Box automatically limits LED brightness to prevent overheating
- Always test your programs with short time intervals first
- Use Ctrl+C to stop any running program
- The status LED shows you if your program is running (blue/green) or has problems (red/yellow)

## Getting Help

If you need more help:
- Check the main `dictionary.md` file for function references
- Look at the MicroPython documentation online
- Ask your teacher or classmates
- Try modifying one small thing at a time

Happy coding! 🌱