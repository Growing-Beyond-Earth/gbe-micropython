# Power-Based Light Control Example

This example demonstrates the new `target_watts` feature that provides consistent light output across different GBE Box hardware versions.

## What This Program Does

- **Night (7 PM - 7 AM)**: All lights off, fan at low speed (40)
- **Day (7 AM - 7 PM)**: Growth spectrum lights with 25.0W power target, medium fan (120)
- **Midday boost (12 PM - 2 PM)**: Intense lights with 35.0W power target, high fan (150)

## Key Features

### Power-Based Control
The `target_watts` parameter automatically adjusts PWM values to achieve precise power consumption:

```json
{
  "red": 80,
  "green": 20, 
  "blue": 40,
  "white": 100,
  "target_watts": 25.0
}
```

This maintains the 80:20:40:100 color ratio while ensuring exactly 25.0W power consumption, regardless of hardware version differences.

### Benefits

1. **Hardware Independence**: Same results on v1.0, v1.4, and v1.5 boards
2. **Research Reproducibility**: Identical power = identical light output
3. **Energy Efficiency**: Precise power control
4. **Color Consistency**: Maintains desired color ratios

## How It Works

1. **Initial Settings**: System starts with specified PWM values (red=80, green=20, etc.)
2. **Power Measurement**: Measures actual power consumption
3. **Automatic Adjustment**: Scales all PWM values proportionally until target power is achieved
4. **Convergence**: Typically achieves target within 2-3 iterations

## Requirements

- **24V Power**: Required for reliable power measurements
- **Minimum Target**: 2.0W minimum for accurate measurement
- **Hardware Limits**: System respects LED safety limits during adjustment

## Fallback Behavior

If power sensor is unavailable or target cannot be achieved:
- Falls back to standard PWM control
- Maintains specified color values
- Logs error message for debugging

## Testing

Use the included test script to verify functionality:

```bash
python test_power_control.py
```

This tests basic power targeting, error handling, and JSON integration.