# Release Notes - Version 2026-06-02

## Reliability Improvements

### I2C Bus Recovery on Startup
`boot.py` now attempts to recover both I2C buses *before* `main.py` constructs any `I2C()` objects. If a bus was left stuck by a previous run (SDA held low by a mid-transfer slave), the recovery routine pulses SCL and issues a STOP to free it, so sensor initialization isn't wedged on boot.

- Succeeds only when both SCL and SDA read high afterward; reports which bus is stuck otherwise.

**Files affected**:
- `boot.py` - Added `i2c_bus_recover()` and run it on both buses during early boot

### Sensor Driver Robustness
- **MPL3115A2**: Initialization no longer raises if the first sample isn't immediately ready. `_read_status()` now polls with a timeout (~1.2 s on init) and tolerates transient I2C errors instead of failing, so a slow-to-warm pressure sensor doesn't abort startup.
- **SCD4x**: `_read_reply()` reads exactly the requested number of bytes via a `memoryview` slice before the CRC check, avoiding over-reads.

**Files affected**:
- `lib/drivers/mpl3115a2.py`, `lib/drivers/scd4x.py`

### Sensor Hot-Plug Detection
I2C1 scanning is now passive — it uses `I2C.scan()` confirmed across multiple consecutive passes rather than writing to every address. This eliminates false add/remove events caused by intrusive probing. The sensor-change monitor interval was also relaxed from 60 s to 300 s.

**Files affected**:
- `lib/gbebox/sensors.py`

## Bug Fixes

### MAC Address Displayed as Zeros
The MAC address was read at import time, before the Pico W's CYW43 radio is powered on, so the startup banner printed `00:00:00:00:00:00`. It is now refreshed from the live WLAN interface in `display_system_info()` after `wifi.connect()` has activated the radio.

**Files affected**:
- `lib/gbebox/hardware.py`

## Improvements

### Startup Banner Cleanup
- WiFi connection status moved onto its own line directly below `Hardware ID`, aligned with the rest of the system info block.
- Removed the redundant IP address from the WiFi status line (it is already shown on the `IP Address` line).

**Files affected**:
- `main.py`, `lib/gbebox/hardware.py`, `lib/gbebox/networking.py`

## Files Changed

- `boot.py` - I2C bus recovery before I2C objects are created
- `lib/drivers/mpl3115a2.py` - Non-fatal status polling with timeout
- `lib/drivers/scd4x.py` - Exact-length reply read via memoryview
- `lib/gbebox/sensors.py` - Passive I2C1 scan with confirmation, longer monitor interval
- `lib/gbebox/hardware.py` - MAC refresh after radio is up, WiFi line in system info
- `lib/gbebox/networking.py` - Connect message no longer includes the IP
- `main.py` - WiFi status passed to and printed by the system info block
- `version.txt` - Bumped to 2026-06-02

### No Breaking Changes
All changes are backward compatible. Existing programs and configurations continue to work without modification.

## Known Issues

None at this time.

---

# Release Notes - Version 2025-10-13

## Critical Fixes

### ⚠️ Timekeeping Bug Fix (CRITICAL)
Fixed a critical bug in I2C RTC datetime handling that caused incorrect time calculations. The bug occurred when converting between I2C RTC and MCU datetime formats - the weekday field at position 3 was incorrectly included in time calculations, leading to time offset errors.

**Impact**: Systems using I2C RTC (DS3231) for timekeeping may have experienced incorrect timestamps in data logs and scheduling errors.

**Files affected**:
- `lib/gbebox/clock.py` - Fixed `sync_rtc_from_utc()` and `sync_rtc_to_utc()` methods to properly skip weekday field when extracting date/time components

### Startup Error Fixes
- **Fixed circular import error** during initialization that prevented system boot with error: `can't import name sd`
  - Added `_initial_boot` flag to prevent WiFi/time operations during SD card initialization
  - Resolves timing conflict between storage and networking module initialization

- **Fixed missing ClockManager methods** error on startup
  - Restored manual time adjustment methods: `_read_manual_time_setting()`, `_apply_manual_time_setting()`, `_clear_manual_time_setting()`
  - Merged critical features from backup while preserving RTC bug fixes

## New Features

### Manual Time Setting Support
Added support for manual time configuration via SD card for systems without WiFi or NTP access.

**Usage**: Create or edit `/sd/set_clock.json` with:
```json
{
  "date": "2025-10-13",
  "time": "14:30:00",
  "utc_offset": "-5.0"
}
```

The system will:
1. Apply the manual time setting on next boot or SD card insertion
2. Update both MCU (local time) and I2C RTC (UTC time)
3. Clear the settings file after successful application
4. Fall back to NTP if manual setting fails

**Files affected**:
- `lib/gbebox/clock.py` - Added manual time setting methods
- `lib/gbebox/storage.py` - Added check for manual time settings on SD card insertion
- `README.md` - Updated configuration documentation

## Improvements

### Power-Based Control Enhancements
Improved power-based LED control to prevent repeated error messages and unnecessary retry attempts.

**Changes**:
- All power control failure cases now cache their results
- Error messages only appear once per unique target_watts value
- System falls back to standard PWM control without repeated attempts
- Cache automatically clears when program settings change

**Failure types now cached**:
- Insufficient voltage (< 20V)
- Power sensor not available
- Sensor communication errors
- Unable to get valid power readings
- Hardware limits reached
- Maximum iterations without convergence

**Files affected**:
- `lib/gbebox/actuators.py` - Added failure caching to all error paths
- `lib/application/logic.py` - Updated cache checking logic

### Program Reload Improvements
Fixed issue where program changes from cloud updates or SD card modifications weren't immediately applied to hardware.

**Changes**:
- `refresh_program_hash()` now clears all cached execution state
- Sensor condition cache cleared on program change
- Power control cache cleared on program change
- New program settings immediately applied without requiring reboot

**Impact**: Cloud-pushed program updates and SD card hot-swap changes now take effect within seconds instead of requiring manual reboot.

**Files affected**:
- `lib/application/logic.py` - Enhanced `refresh_program_hash()` to clear cached state

## Bug Fixes

### SD Card Hot-Swap
- Fixed WiFi reconnection triggering during initial boot (now only occurs on SD card reinsertion)
- Fixed manual time check running before storage system fully initialized

### Hardware Configuration
- Updated LED channel hardware limits to current specifications:
  - Red: 240 (was 160)
  - Green: 82 (was 71)
  - Blue: 99 (was 75)
  - White: 196 (was 117)

## Documentation Updates

- Updated `README.md` to include `set_clock.json` configuration
- Corrected WiFi configuration filename from `wifi.json` to `wifi_settings.json`
- Added manual time setting documentation

## Technical Details

### Time Architecture Clarification
The system maintains a clear separation of time storage:
- **I2C RTC (DS3231)**: Stores UTC time for persistence across reboots
- **MCU RTC (RP2040)**: Stores local time for program execution
- **Priority order**: Manual setting → NTP → I2C RTC → MCU time

### Cache Management
The system now maintains two levels of cache:
1. **Execution cache** (cleared on program change):
   - Sensor condition evaluation results
   - Power control target and results

2. **Program cache** (persisted until change):
   - Program JSON hash for cloud sync
   - Current program configuration

## Files Changed

### Modified:
- `lib/gbebox/clock.py` - RTC bug fixes, manual time features
- `lib/gbebox/storage.py` - Circular import fix, initialization guard
- `lib/gbebox/actuators.py` - Power control caching, hardware limits
- `lib/application/logic.py` - Program reload improvements, cache management
- `README.md` - Configuration documentation updates

### No Breaking Changes
All changes are backward compatible. Existing programs and configurations will continue to work without modification.

## Upgrade Instructions

1. Backup your SD card configuration files
2. Copy new software to Pico W
3. Reboot the system
4. Verify time synchronization is working correctly
5. (Optional) Create `set_clock.json` for manual time setting

## Known Issues

None at this time.

---

**Released**: October 13, 2025
**Developed by**: Fairchild Tropical Botanic Garden
**Project**: Growing Beyond Earth® (GBE)
