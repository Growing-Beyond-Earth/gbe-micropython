# Basic LED Light Control Example
# This example shows how to control the RGBW LED panel on your GBE Box
# Run this program to see different lighting effects

import gbebox
import time

print("Starting LED control example...")

# Turn on the status LED to show the program is running
gbebox.indicator.on("blue")

# Example 1: Turn lights on with default settings (soft white light)
print("1. Turning on lights with default settings...")
gbebox.light.on()
time.sleep(3)  # Wait 3 seconds so you can see the effect

# Example 2: Turn lights off
print("2. Turning lights off...")
gbebox.light.off()
time.sleep(2)

# Example 3: Set individual color channels
print("3. Setting individual colors...")
gbebox.light.red(50)    # Red channel: 0-160 max (safe limit to prevent overheating)
gbebox.light.green(30)  # Green channel: 0-71 max
gbebox.light.blue(20)   # Blue channel: 0-75 max  
gbebox.light.white(0)   # White channel: 0-117 max (turn off white for pure color)
time.sleep(3)

# Example 4: Set all RGBW channels at once
print("4. Setting all colors at once to create purple light...")
gbebox.light.rgbw(80, 0, 60, 0)  # Red + Blue = Purple
time.sleep(3)

# Example 5: Get current color values and display them
print("5. Reading current color values...")
r, g, b, w = gbebox.light.rgbw()  # Get all current values
print(f"Current colors - Red: {r}, Green: {g}, Blue: {b}, White: {w}")
time.sleep(2)

# Example 6: Create a simple sunrise effect
print("6. Creating sunrise effect...")
for brightness in range(0, 60, 5):  # Gradually increase from 0 to 60
    # Mix red, yellow, and white for sunrise colors
    red_amount = brightness
    green_amount = brightness // 2  # Half as much green for orange tint
    white_amount = brightness
    
    gbebox.light.rgbw(red_amount, green_amount, 0, white_amount)
    print(f"Brightness level: {brightness}")
    time.sleep(1)  # Wait 1 second between changes

print("7. Returning to soft white light...")
gbebox.light.on()  # Back to default soft white

# Change status LED to green to show program completed successfully
gbebox.indicator.on("green")
print("LED control example completed!")