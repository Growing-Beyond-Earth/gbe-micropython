# GBE Box Program JSON Format

## What is the Program File?

The `program.json` file is like a **recipe book** for your GBE Box. Instead of you having to manually turn lights on and off or adjust the fan speed all day, this file tells your GBE Box exactly what to do and when to do it - automatically!

Think of it like programming a smart thermostat in your house, but for plants. You can create rules like:
- "Turn the lights on at 7 AM and off at 7 PM"
- "If it gets too hot, speed up the fan" 
- "During summer, use brighter lights than in spring"

## Why JSON Format?

**JSON** stands for "JavaScript Object Notation" - but don't worry, you don't need to know JavaScript! JSON is just a simple way to organize information that both humans and computers can easily understand.

JSON uses a structure similar to making lists and filling out forms:
- **Lists** are written with square brackets `[ ]`
- **Information forms** are written with curly braces `{ }`  
- **Labels and values** are connected with colons `:`

**Want to learn more about JSON?** Check out these beginner-friendly resources:
- [JSON Introduction (W3Schools)](https://www.w3schools.com/js/js_json_intro.asp) - Simple tutorial with examples
- [What is JSON? (Mozilla)](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/JSON) - More detailed explanation

## What Can Your Program Do?

Your `program.json` file can create automation rules that control the GBE Box's LED lights and fan based on:

- **Time schedules** - Create day/night cycles (photoperiods)
- **Date ranges** - Different settings for different seasons or growth phases  
- **Sensor conditions** - Respond to temperature, humidity, CO2, and other measurements
- **Default settings** - Fallback values when no other conditions apply

The best part? You can combine all of these together to create sophisticated growing environments that automatically adjust to give your plants exactly what they need!

## File Structure (The Basic Recipe)

Every `program.json` file follows the same basic pattern - like a recipe template:

```json
{
  "settings": {
    "default_actions": [ ... ],
    "loops": [ ... ]
  }
}
```

Think of this structure like organizing a cookbook:

### `"settings"` - The Main Recipe Section
This is where all your automation rules live.

### `"default_actions"` - What to Do Normally  
These are the basic settings your GBE Box uses when nothing special is happening. Like the "everyday" settings - maybe lights off and fan on low speed.

### `"loops"` - Special Rules and Conditions
This is where you write rules like "IF it's daytime THEN turn lights on" or "IF temperature is too high THEN speed up the fan." These rules can override your default settings when their conditions are met.

**Think of it this way:**
- **Default actions** = "What should I normally do?"
- **Loops** = "But if this happens, do this instead!"

---

## Default Actions (Your "Normal" Settings)

Default actions are what your GBE Box does when no special conditions are happening. Think of these as your "baseline" or "normal" settings that are always running in the background.

```json
"default_actions": [
  {
    "red": 0,
    "green": 0,
    "blue": 0,
    "white": 0,
    "fan": 96
  }
]
```

In this example, the default is to have all lights off (0) but keep the fan running at medium speed (96) for air circulation.

### What You Can Control:

| Setting | What It Does | Range | Examples |
|---------|--------------|--------|----------|
| `red` | Red LED brightness | 0-160 | 0 = off, 80 = medium, 160 = maximum |
| `green` | Green LED brightness | 0-71 | 0 = off, 35 = medium, 71 = maximum |
| `blue` | Blue LED brightness | 0-75 | 0 = off, 40 = medium, 75 = maximum |
| `white` | White LED brightness | 0-117 | 0 = off, 60 = medium, 117 = maximum |
| `fan` | Fan speed | 0-255 | 0 = off, 128 = medium, 255 = maximum |
| `target_watts` | Target power consumption (optional) | 2.0+ | Automatically adjusts PWM values to achieve target power |

### Hardware Protection
The LED limits (like red maxing out at 160 instead of 255) are **hardware protection limits** built by the LED manufacturer to prevent component damage from overheating. If you try to set red to 200, the GBE Box will automatically reduce it to 160 to protect the LED hardware.

### Power-Based Light Control (target_watts)

The optional `target_watts` parameter provides **consistent light output** across different GBE Box hardware versions by automatically adjusting PWM values to achieve a specific power consumption target.

#### How It Works:
1. **Set initial PWM values** for desired color balance (red, green, blue, white)
2. **Specify target power** consumption in watts using `target_watts`
3. **System automatically adjusts** all PWM values proportionally until actual power consumption matches the target
4. **Maintains color ratios** while ensuring consistent light intensity

#### Benefits:
- **Hardware independence**: Same results across v1.0, v1.4, and v1.5 boards
- **Research reproducibility**: Identical power consumption = identical light output
- **Energy efficiency**: Precise power control for consistent experiments

#### Usage Notes:
- **Minimum power**: Target must be ≥2.0W for reliable measurement
- **Hardware limits**: System respects LED safety limits during adjustment
- **Fallback behavior**: If power sensor unavailable, uses standard PWM control
- **Optional feature**: Can use PWM-only control by omitting `target_watts`

#### Example:
```json
{
  "red": 80,
  "green": 20, 
  "blue": 40,
  "white": 100,
  "target_watts": 25.0
}
```
This maintains the 80:20:40:100 color ratio while adjusting all values to achieve exactly 25.0W power consumption.

---

## Loop Types

The `loops` array contains conditional rules that can be time-based, date-based, or sensor-based.

### Time-Based Loops

Control hardware based on daily schedules (photoperiods).

```json
{
  "type": "time",
  "start": "07:00",
  "end": "19:00",
  "actions": [
    {
      "red": 10,
      "green": 0,
      "blue": 30,
      "white": 115,
      "target_watts": 23.5
    }
  ]
}
```

#### Time Loop Parameters:

| Parameter | Type | Format | Description |
|-----------|------|---------|-------------|
| `type` | string | "time" | Identifies this as a time-based rule |
| `start` | string | "HH:MM" | Start time (24-hour format) |
| `end` | string | "HH:MM" | End time (24-hour format) |
| `actions` | array | [action objects] | Hardware settings to apply during this time period |

#### Time Examples:
- `"07:00"` to `"19:00"` = Daytime lighting (7 AM to 7 PM) - **Standard GBE setup**
- `"19:00"` to `"07:00"` = Nighttime settings (spans midnight)
- `"12:00"` to `"14:00"` = Midday boost period

### Date-Based Loops

Control hardware based on calendar date ranges (useful for seasonal experiments or growth phases).

```json
{
  "type": "date_range",
  "start_date": "2024-03-01",
  "end_date": "2024-05-31",
  "actions": [
    {
      "red": 120,
      "green": 30,
      "blue": 60,
      "white": 80
    }
  ]
}
```

#### Date Loop Parameters:

| Parameter | Type | Format | Description |
|-----------|------|---------|-------------|
| `type` | string | "date_range" | Identifies this as a date-based rule |
| `start_date` | string | "YYYY-MM-DD" | Start date (ISO format) |
| `end_date` | string | "YYYY-MM-DD" | End date (optional - omit for open-ended) |
| `actions` | array | [action objects] | Hardware settings to apply during this date range |

#### Date Examples:
- `"2024-01-01"` to `"2024-03-31"` = Winter growing season
- `"2024-06-01"` to `"2024-08-31"` = Summer experimental period  
- `"2024-09-15"` to `null` = Open-ended from September 15th onward
- `"2024-02-14"` to `"2024-02-14"` = Single day special conditions

### Sensor-Based Loops

Control hardware based on real-time sensor readings.

```json
{
  "type": "sensor",
  "condition": {
    "sensor": "humidity",
    "comparison": "<",
    "value": 60
  },
  "actions": [
    {
      "fan": 0
    }
  ]
}
```

#### Sensor Loop Parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | "sensor" - Identifies this as a sensor-based rule |
| `condition` | object | Defines when this rule should activate |
| `actions` | array | Hardware settings to apply when condition is met |

#### Condition Object:

| Parameter | Type | Options | Description |
|-----------|------|---------|-------------|
| `sensor` | string | See sensor types below | Which sensor to monitor |
| `comparison` | string | `"<"`, `">"`, `"<="`, `">="`, `"=="` | Comparison operator |
| `value` | number | Depends on sensor | Threshold value for comparison |

#### Available Sensors:

| Sensor Name | Unit | Description | Typical Range |
|-------------|------|-------------|---------------|
| `"temperature"` | °C | Air temperature | 15-35°C |
| `"humidity"` | % | Relative humidity | 30-90% |
| `"co2"` | ppm | Carbon dioxide concentration | 300-2000 ppm |
| `"pressure"` | Pa | Atmospheric pressure | 98000-102000 Pa |
| `"lux"` | lux | Light intensity | 0-50000 lux |
| `"voltage"` | V | System voltage | 4.5-5.5 V |
| `"current"` | mA | System current draw | 100-3000 mA |
| `"power"` | W | System power consumption | 0.5-15 W |
| `"fan_speed"` | RPM | Fan rotation speed | 0-3000 RPM |
| `"moisture"` | - | Soil moisture level | 0-1000 |

---

## Complete Examples

### Example 1: Basic Day/Night Cycle

```json
{
  "settings": {
    "default_actions": [
      {
        "red": 0,
        "green": 0,
        "blue": 0,
        "white": 0,
        "fan": 50
      }
    ],
    "loops": [
      {
        "type": "time",
        "start": "07:00",
        "end": "19:00",
        "actions": [
          {
            "red": 80,
            "green": 20,
            "blue": 40,
            "white": 100,
            "fan": 120
          }
        ]
      }
    ]
  }
}
```

**What this does:**
- **Night (7 PM - 7 AM)**: All lights off, fan at low speed (50)
- **Day (7 AM - 7 PM)**: Growth spectrum lights on, fan at medium speed (120)

### Example 2: Temperature-Responsive Cooling

```json
{
  "settings": {
    "default_actions": [
      {
        "red": 60,
        "green": 15,
        "blue": 30,
        "white": 90,
        "fan": 80
      }
    ],
    "loops": [
      {
        "type": "sensor",
        "condition": {
          "sensor": "temperature",
          "comparison": ">",
          "value": 26
        },
        "actions": [
          {
            "fan": 200
          }
        ]
      },
      {
        "type": "sensor", 
        "condition": {
          "sensor": "temperature",
          "comparison": ">",
          "value": 28
        },
        "actions": [
          {
            "red": 40,
            "green": 10,
            "blue": 20,
            "white": 60,
            "fan": 255
          }
        ]
      }
    ]
  }
}
```

**What this does:**
- **Normal**: Growth lights at moderate levels, fan at speed 80
- **Above 26°C**: Fan increases to speed 200 for cooling  
- **Above 28°C**: Lights dim to reduce heat, fan at maximum speed

### Example 3: Seasonal Growth with Nested Time Controls

```json
{
  "settings": {
    "default_actions": [
      {
        "red": 0,
        "green": 0,
        "blue": 0,
        "white": 0,
        "fan": 50
      }
    ],
    "loops": [
      {
        "type": "date_range",
        "start_date": "2024-03-01",
        "end_date": "2024-05-31",
        "actions": [
          {
            "fan": 80
          }
        ],
        "loops": [
          {
            "type": "time",
            "start": "07:00",
            "end": "19:00",
            "actions": [
              {
                "red": 60,
                "green": 20,
                "blue": 40,
                "white": 70
              }
            ]
          }
        ]
      },
      {
        "type": "date_range", 
        "start_date": "2024-06-01",
        "end_date": "2024-08-31",
        "actions": [
          {
            "fan": 100
          }
        ],
        "loops": [
          {
            "type": "time",
            "start": "07:00",
            "end": "19:00",
            "actions": [
              {
                "red": 120,
                "green": 30,
                "blue": 60,
                "white": 100
              }
            ]
          }
        ]
      }
    ]
  }
}
```

**What this does:**
- **Default**: All lights off, base fan speed (50)
- **Spring (Mar-May)**: Medium fan speed (80), moderate lights during day (7 AM - 7 PM)
- **Summer (Jun-Aug)**: Higher fan speed (100), intense lights during day (7 AM - 7 PM)
- **All nights**: Lights automatically off, fan returns to date-specific setting

### Example 4: Advanced Multi-Condition with Nested Sensor Controls

```json
{
  "settings": {
    "default_actions": [
      {
        "red": 0,
        "green": 0,
        "blue": 0,
        "white": 0,
        "fan": 40
      }
    ],
    "loops": [
      {
        "type": "time",
        "start": "07:00",
        "end": "19:00",
        "actions": [
          {
            "red": 100,
            "green": 25,
            "blue": 50,
            "white": 80,
            "fan": 90
          }
        ],
        "loops": [
          {
            "type": "sensor",
            "condition": {
              "sensor": "humidity",
              "comparison": "<",
              "value": 50
            },
            "actions": [
              {
                "fan": 0
              }
            ],
            "loops": [
              {
                "type": "sensor",
                "condition": {
                  "sensor": "temperature",
                  "comparison": ">",
                  "value": 26
                },
                "actions": [
                  {
                    "fan": 150
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

**What this does:**
- **Night (7 PM - 7 AM)**: Lights off, minimal fan (40)
- **Day (7 AM - 7 PM)**: Growth lights on, normal fan speed (90)
  - **If humidity < 50%**: Turn off fan to conserve moisture (0)
    - **But if temperature > 26°C**: Override humidity rule and turn on fan for cooling (150)

**Why this makes sense:**
- **Humidity control**: Turning off the fan when humidity is low prevents moisture loss
- **Temperature override**: Even with low humidity, cooling is prioritized when too hot
- **Nested logic**: Temperature sensor overrides humidity sensor because overheating is more dangerous than dry air

---

## Nested Loops

Loops can contain other loops using the `"loops"` property. This creates hierarchical control where inner loops override outer loops when their conditions are met.

### Nesting Structure:
```json
{
  "type": "date_range",
  "start_date": "2024-06-01", 
  "end_date": "2024-08-31",
  "actions": [{"fan": 80}],
  "loops": [
    {
      "type": "time",
      "start": "07:00",
      "end": "19:00", 
      "actions": [{"red": 100, "white": 80}],
      "loops": [
        {
          "type": "sensor",
          "condition": {"sensor": "temperature", "comparison": ">", "value": 26},
          "actions": [{"fan": 200}]
        }
      ]
    }
  ]
}
```

### Nesting Rules:
- **Any loop type** can contain nested loops
- **Nested loops inherit** the context of their parent loop
- **Inner loops only activate** when their parent loop is already active
- **Deeper nesting** has higher priority

---

## Rule Priority and Interaction

### How Multiple Conditions Work:
1. **Default actions** are always active as the baseline
2. **Date-based loops** override defaults when current date falls within their range
3. **Time-based loops** override defaults and date loops during their active periods  
4. **Sensor-based loops** override other types when conditions are met
5. **Nested loops** have higher priority than their parent loops
6. **Deeper nesting levels** override shallower levels
7. **Within the same level**, later loops override earlier loops for conflicting parameters

### Parameter Merging:
If multiple rules affect different parameters, they combine:
```json
// Time loop sets lights, sensor loop sets fan
"Final result": {
  "red": 80,    // from time loop
  "white": 100, // from time loop  
  "fan": 200    // from temperature sensor loop
}
```

If multiple rules affect the same parameter, the most recent/specific wins:
```json
// Both loops set fan speed - sensor loop wins
"fan": 200  // from sensor loop, overrides time loop value
```

---

## Validation and Error Handling

### Required Fields:
- All loops must have `type` and `actions`
- Time loops must have `start` and `end`
- Date loops must have `start_date` (end_date is optional)
- Sensor loops must have complete `condition` object
- Actions must contain at least one hardware parameter

### Invalid Values:
- LED values above safety limits are automatically clamped
- Fan speeds outside 0-255 range are clamped
- Invalid time formats default to "00:00"
- Unknown sensors are ignored
- Invalid comparisons default to "=="

### File Loading:
- Missing `program.json` loads from `/defaults/program.json`
- Corrupted JSON files fall back to defaults
- Parsing errors are logged but don't crash the system

---

## Tips for Students

### Creating Effective Programs:

1. **Start simple**: Begin with just time-based day/night cycles
2. **Test incrementally**: Add one sensor condition at a time
3. **Use realistic values**: Check sensor ranges before setting thresholds
4. **Consider plant needs**: Different crops have different optimal conditions
5. **Monitor results**: Check data logs to see if programs work as expected

### Common Patterns:

**Photoperiod Control:**
```json
"start": "08:00", "end": "16:00"  // 8-hour day for short-day plants
"start": "06:00", "end": "18:00"  // 12-hour day for neutral plants  
"start": "05:00", "end": "19:00"  // 14-hour day for long-day plants
```

**Temperature Management:**
```json
"condition": {"sensor": "temperature", "comparison": ">", "value": 25}  // Cooling
"condition": {"sensor": "temperature", "comparison": "<", "value": 18}  // Warming
```

**Growth Optimization:**
```json
"red": 80, "blue": 60, "white": 40  // Vegetative growth spectrum
"red": 120, "blue": 40, "white": 80  // Flowering spectrum
```

---

## Troubleshooting

### Program Not Working:
- Check JSON syntax with online validator
- Verify time format is "HH:MM" (24-hour)
- Ensure sensor names match exactly (case-sensitive)
- Check that required sensors are connected

### Unexpected Behavior:
- Review rule priority (sensor > time > default)
- Check for conflicting conditions
- Verify threshold values are realistic
- Monitor system logs for error messages

### Performance Issues:
- Limit number of sensor loops (max 10 recommended)
- Avoid extremely frequent condition changes
- Use reasonable sensor check intervals
- Consider system memory limitations

For more help, see the example programs in the `examples/` folder and the complete function reference in `dictionary.md`.