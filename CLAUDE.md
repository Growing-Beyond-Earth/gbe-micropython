# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

MicroPython firmware for the **Growing Beyond Earth® (GBE)** control circuit — a Raspberry Pi Pico W that runs a tabletop plant growth chamber (RGBW LED panel, fan, optional 12V pump, and environmental sensors). It is built by Fairchild Tropical Botanic Garden in partnership with NASA, and is designed to be programmed by middle/high school students through the simple `gbebox` API.

There is **no build, lint, or test harness** in this repo. Code runs only on real Pico W hardware (or a compatible MicroPython REPL). Development is done by copying files to the Pico's root filesystem and running via Thonny or a serial REPL.

## Running and deploying

- Deploy by copying the repo's files to the Pico W root: `boot.py`, `main.py`, `version.txt`, `board.json`, and the `lib/` directory (which must land on the MicroPython path, i.e. `/lib`). `examples/` and `defaults/` are optional helpers.
- `boot.py` runs first on every power-up: resets actuator pins to a safe state, blanks the NeoPixel, and performs **I2C bus recovery** on both buses *before* any `I2C()` object is constructed. Don't move I2C bus creation earlier than this.
- `main.py` is the entry point: it builds an asyncio event loop and `run_forever()`. All runtime behavior (program execution, logging, watchdog, GC, sensor hot-plug, WiFi reconnect) is a set of cooperative `asyncio` tasks created in `main()`.
- To test interactively, run `import gbebox` in the REPL and call API methods (e.g. `gbebox.light.on()`, `gbebox.sensor.temperature()`). See `DICTIONARY.md` for the full student-facing function reference.

## Architecture

The public surface is the **`gbebox` package** (`lib/gbebox/__init__.py`), which imports submodules and re-exports a flat set of singleton objects. Student code only ever touches these singletons:

| Object | Module | Role |
|---|---|---|
| `light`, `fan` | `actuators.py` | RGBW PWM channels and fan PWM/RPM control |
| `sensor` | `sensors.py` | Unified reader across all environmental sensors |
| `indicator` | `indicator.py` | NeoPixel status LED effects (async) |
| `sd` | `storage.py` | SD card mount + JSON config management |
| `wifi`, `wlan` | `networking.py` | WiFi connect / reconnect |
| `clock` | `clock.py` | NTP sync, timezone, local-time math |
| `Run` / `ProgramEngine` | `application/logic.py` | Automated program execution + logging |

Key cross-cutting patterns:

- **Singletons created at import time.** Most modules instantiate a manager class and export the instance (e.g. `board_config = BoardConfig()` in `hardware.py`, then `light = LightController()`, `sensor = SensorManager()`). Importing `gbebox` initializes hardware. Many internal functions use **function-level imports** specifically to avoid circular-import problems between these modules — keep that pattern when adding cross-module calls.
- **Hardware abstraction (`hardware.py`).** `board.json` defines all pin assignments and is the single source of truth for wiring. `BoardConfig` builds the `i2c0`, `i2c1`, `spi0`, and `led` interfaces from it. Two I2C buses are used deliberately: **I2C0 = onboard** (INA219 power monitor, version-detect EEPROM); **I2C1 = optional/external sensors** (SHT35, SCD4x CO2, MPL3115A2, VEML7700 lux, Seesaw soil).
- **Hardware version detection (`drivers/version_detect.py`).** On boot, `detect_and_configure_hardware()` identifies the board revision (v1.0 / v1.4 / v1.5) — by EEPROM presence on I2C0, falling back to an LED power-draw test — and picks the correct INA219 shunt-resistor (`RSH`) value so power/current readings are accurate. The result is cached in `/cache/hardware_version.json`. The `hardware_date` derived from this is reported to the cloud.
- **Graceful sensor degradation (`sensors.py`).** All sensor drivers are loaded dynamically via `load_libraries()`; a missing or failing driver yields `None` rather than crashing. `SensorReading` wraps every reading with retry-on-`OSError/RuntimeError`. `sensor.temperature` (and friends) pick the best available source by priority (e.g. SHT35 > MPL3115A2 > SCD4x). `sensor.all` returns the dict of every reading used for logging. Sensors are hot-pluggable — `monitor_sensor_changes()` re-scans I2C1.
- **Program engine (`application/logic.py`).** `ProgramEngine.run()` is the control loop. It reads `program.json` (from the SD card via `sd.program_json`) and, each second, computes desired RGBW + fan + optional `target_watts` from a tree of **loops** (`time`, `date_range`, `sensor`, nestable) merged over `default_actions`, then applies only the deltas. Sensors are evaluated on a slower `sensor_check_interval` and cached between checks. `target_watts` triggers closed-loop power control via `light.set_rgbw_with_power_target()` instead of raw PWM. See `PROGRAM_JSON_FORMAT.md` for the full schema.
- **Data logging + cloud sync (`DataLogger` in logic.py).** Every `log_interval` (default 600s) it writes a CSV row to `/sd/log.csv` and POSTs JSON to `growingbeyond.earth`. The server response can push a **program replacement** (saved back to SD) or signal a `prog_hash` mismatch (triggers re-upload of the local program). Program identity is a `jsum` SHA1 hash, recomputed via a registered callback when the SD program changes. Uploads are skipped under low free memory.
- **Reliability tasks.** `WatchdogManager` feeds an 8.4s hardware `WDT` (only when not USB-connected, so development isn't interrupted). `GarbageCollector` runs `gc.collect()` every couple seconds — this is memory-constrained hardware, so explicit `gc.collect()` calls before large allocations (uploads, data collection) are intentional. `boot.py`/`main.py` also implement a USB-power-cycle gesture that enters the bootloader for firmware flashing.

## Layout

- `lib/gbebox/` — the public API package (the singletons above).
- `lib/application/` — `logic.py` (engine/logger/watchdog/GC) and `utils.py` (`calc` time/date helpers used by the program engine).
- `lib/drivers/` — one module per sensor/peripheral chip (SCD4x, SHT35, INA219, VEML7700, MPL3115A2, DS3231 RTC, Seesaw soil, SD card, fan RPM, core temp) plus `version_detect.py`.
- `lib/json_utils/` — `jpretty` (pretty-print) and `jsum` (stable hashing for program identity).
- `defaults/` — template config files (`program.json`, `wifi_settings.json`, `timezone.json`, `set_clock.json`) that are normally placed on the SD card, **not** in flash.
- `cache/` — runtime state on the device (`lastrun.json`, `hardware_version.json`); generally empty in the repo.
- `examples/` — numbered student programs; `DICTIONARY.md` documents the API; `PROGRAM_JSON_FORMAT.md` documents the program schema.

## Conventions

- Target is MicroPython, not CPython: use `uasyncio`, `urequests`, `uos`, `ubinascii`, `machine`, `network`, `time.sleep_ms/sleep_us`. Standard CPython-only libraries are unavailable.
- Code is read by students — keep inline comments and clear naming consistent with the existing files.
- Many classes carry explicit "backward compatibility" shims (e.g. `Run` wraps `ProgramEngine`, `system`/`gc` aliases). Preserve existing public names when refactoring.
- `version.txt` holds the software release date string surfaced as `gbebox.software_date` and reported to the cloud; bump it on releases.
- Per global instruction: **always ask before committing.**
