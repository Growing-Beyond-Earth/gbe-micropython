"""
Program execution engine for GBE Box.

Handles automated program execution, logging, watchdog, and garbage collection.
"""

import uasyncio as asyncio
import time
import gc
import json
import urequests
import machine
from machine import WDT
import uos
from json_utils import jsum


class ProgramEngine:
    """
    Main program execution engine.
    
    Orchestrates automated environmental control based on JSON program configuration.
    """
    
    def __init__(self, log_interval=600, sensor_check_interval=60):
        self.log_interval = log_interval
        self.sensor_check_interval = sensor_check_interval
        self.last_sensor_check_time = 0
        self.cached_sensor_conditions = None
        
        
        # Initialize sub-components
        self.watchdog = WatchdogManager()
        self.logger = DataLogger(self, log_interval)
        self.gc_manager = GarbageCollector()
        # For backward compatibility
        self.gc = self.gc_manager
    
    @property
    def program_json(self):
        """Get current program configuration."""
        from gbebox.storage import sd
        return sd.program_json
    
    async def run(self):
        """Main program execution loop."""
        if not self.program_json:
            print("No program configuration loaded")
            return
        
        print("Starting program execution loop...")
        
        while True:
            try:
                current_time = time.time()
                
                # Apply conditions without checking sensors
                await self._determine_and_apply_conditions(self.program_json, check_sensors=False)
                
                # Check sensors at defined intervals
                if current_time - self.last_sensor_check_time >= self.sensor_check_interval:
                    await self._determine_and_apply_conditions(self.program_json, check_sensors=True)
                    self.last_sensor_check_time = current_time
                
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error in program execution loop: {e}")
                # Continue running even if there's an error
                await asyncio.sleep(5)  # Wait a bit longer after an error
    
    async def _determine_and_apply_conditions(self, json_data, check_sensors=False):
        """Determine and apply the necessary environmental conditions."""
        from gbebox.actuators import light, fan
        
        # Get current hardware state
        current_rgbw = light.rgbw()
        current_fan = fan.setting()
        
        # Determine desired conditions
        desired = await self._determine_desired_conditions(
            json_data["settings"].get("loops", []), 
            current_rgbw, 
            current_fan, 
            check_sensors
        )
        
        # Apply changes if needed
        if desired.get("target_watts") is not None:
            # Power-based control - check if target or initial PWM values changed
            target_watts = desired["target_watts"]
            r, g, b, w = desired["rgbw"]
            
            # Check if this is the same power target we already achieved
            if (hasattr(light, '_last_power_target') and 
                light._last_power_target == target_watts and
                light._last_power_result is not None and
                light._last_power_result.get('success', False)):
                # Target already achieved, no need to adjust
                pass
            else:
                # New target or failed previous attempt - run power adjustment
                result = await light.set_rgbw_with_power_target(r, g, b, w, target_watts)
                
                if not result['success']:
                    print(f"Power-based control failed: {result['error']}")
                    # Fall back to standard PWM control
                    light.rgbw(*desired["rgbw"])
                else:
                    print(f"Power-based control succeeded: {result['actual_power']:.1f}W target {result['target_power']:.1f}W")
        elif desired["rgbw"] != current_rgbw:
            # Standard PWM control only when no target_watts
            light.rgbw(*desired["rgbw"])
        
        if desired["fan"] != current_fan:
            fan.setting(desired["fan"])
    
    async def _determine_desired_conditions(self, loops, current_rgbw, current_fan, check_sensors):
        """Determine desired environmental conditions based on program logic."""
        from .utils import calc
        
        # Start with default conditions
        default_actions = self.program_json["settings"].get("default_actions", [])
        if default_actions:
            desired = self._extract_conditions(default_actions)
        else:
            desired = {"rgbw": [0, 0, 0, 0], "fan": 0, "target_watts": None}
        
        # Process all loops and override with active conditions
        for loop in loops:
            loop_type = loop.get("type")
            
            if loop_type == "sensor":
                if check_sensors:
                    condition_met, actions = await self._evaluate_sensor_condition(loop)
                    if condition_met:
                        sensor_conditions = self._extract_conditions(actions)
                        self.cached_sensor_conditions = sensor_conditions
                    else:
                        self.cached_sensor_conditions = None
                        sensor_conditions = {}
                else:
                    sensor_conditions = self.cached_sensor_conditions or {}
                
                if sensor_conditions:
                    desired = self._merge_conditions(desired, sensor_conditions)
            
            elif loop_type == "time":
                start_time = loop.get("start", "00:00")
                end_time = loop.get("end", "23:59")
                
                if calc.time_within_range(start_time, end_time):
                    time_conditions = self._extract_conditions(loop.get("actions", []))
                    desired = self._merge_conditions(desired, time_conditions)
                    
                    # Process nested loops
                    if "loops" in loop:
                        nested_desired = await self._determine_desired_conditions(
                            loop["loops"], desired["rgbw"], desired["fan"], check_sensors
                        )
                        desired = nested_desired
            
            elif loop_type == "date_range":
                start_date = loop.get("start_date", calc.current_date())
                end_date = loop.get("end_date", None)
                
                if calc.date_within_range(calc.current_date(), start_date, end_date):
                    date_conditions = self._extract_conditions(loop.get("actions", []))
                    desired = self._merge_conditions(desired, date_conditions)
                    
                    # Process nested loops
                    if "loops" in loop:
                        nested_desired = await self._determine_desired_conditions(
                            loop["loops"], desired["rgbw"], desired["fan"], check_sensors
                        )
                        desired = nested_desired
        
        return desired
    
    async def _evaluate_sensor_condition(self, loop):
        """Evaluate sensor-based condition."""
        try:
            from gbebox.sensors import sensor
            
            condition = loop.get("condition")
            if not condition:
                return False, []
            
            # Get sensor value
            sensor_name = condition.get("sensor")
            if not sensor_name:
                return False, []
            
            # Get the sensor reading function
            sensor_func = getattr(sensor, sensor_name, None)
            if sensor_func is None:
                print(f"Unknown sensor: {sensor_name}")
                return False, []
            
            # Call the sensor function safely
            sensor_reading = sensor_func()
            if sensor_reading is None:
                return False, []
            
            # Evaluate condition
            comparison = condition.get("comparison")
            threshold = condition.get("value")
            
            if comparison == "<" and sensor_reading < threshold:
                return True, loop.get("actions", [])
            elif comparison == ">=" and sensor_reading >= threshold:
                return True, loop.get("actions", [])
            
            return False, []
            
        except Exception as e:
            print(f"Error evaluating sensor condition: {e}")
            return False, []
    
    def _extract_conditions(self, actions):
        """Extract RGBW, fan, and power target settings from action list."""
        rgbw = [None, None, None, None]
        fan_setting = None
        target_watts = None
        
        for action in actions:
            rgbw[0] = action.get("red", rgbw[0])
            rgbw[1] = action.get("green", rgbw[1])
            rgbw[2] = action.get("blue", rgbw[2])
            rgbw[3] = action.get("white", rgbw[3])
            
            if "fan" in action:
                fan_setting = action["fan"]
                
            if "target_watts" in action:
                target_watts = action["target_watts"]
        
        return {"rgbw": rgbw, "fan": fan_setting, "target_watts": target_watts}
    
    def _merge_conditions(self, current, new):
        """Merge new conditions into current conditions."""
        # Only convert to list if we need to modify it
        needs_modification = any(new["rgbw"][i] is not None for i in range(4))
        if needs_modification:
            current["rgbw"] = list(current["rgbw"])
            
            # Merge RGBW values
            for i in range(4):
                if new["rgbw"][i] is not None:
                    current["rgbw"][i] = new["rgbw"][i]
        
        # Merge fan setting
        if new["fan"] is not None:
            current["fan"] = new["fan"]
            
        # Merge target watts setting
        if new["target_watts"] is not None:
            current["target_watts"] = new["target_watts"]
        
        return current
    


class WatchdogManager:
    """Hardware watchdog timer management."""
    
    def __init__(self):
        self.wdt = None
    
    async def start(self):
        """Start the watchdog timer."""
        from gbebox.hardware import led
        
        while True:
            if self.wdt is None:
                self.wdt = WDT(timeout=8388)  # ~8.4 seconds
            
            try:
                self.wdt.feed()
                # Brief LED flash to indicate activity
                led.on()
                await asyncio.sleep(0.01)
                led.off()
            except Exception as e:
                print(f"Watchdog error: {e}")
            
            await asyncio.sleep(0.99)


class GarbageCollector:
    """Memory management through garbage collection."""
    
    async def start(self):
        """Start periodic garbage collection."""
        gc.enable()
        while True:
            gc.collect()
            gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
            await asyncio.sleep(2)  # More frequent GC for memory-constrained operation


class DataLogger:
    """Data logging to SD card and cloud services."""
    
    def __init__(self, program_engine, interval=600):
        self.program_engine = program_engine
        self.interval = interval
        self.log_file_path = '/sd/log.csv'
        self.log_headers = ('Date,Time,Temperature (C),Humidity (%),CO2 (ppm),'
                          'Pressure (Pa),Lux (lx),Voltage (V),Current (mA),'
                          'Power (W),Fan Speed (rpm),Moisture\n')
        
        # Cache program hash to avoid recomputing on every upload
        self._cached_prog_hash = None
        self._compute_program_hash()
        
        self._initialize_log_file()
    
    def _compute_program_hash(self):
        """Compute and cache the program hash."""
        if self.program_engine.program_json:
            try:
                from json_utils import jsum
                self._cached_prog_hash = jsum.digest(self.program_engine.program_json, 
                                                   hash_algorithm='sha1', encoding='base64')
            except Exception as e:
                print(f"Error computing program hash: {e}")
                self._cached_prog_hash = None
        else:
            self._cached_prog_hash = None
    
    def refresh_program_hash(self):
        """Refresh the cached program hash when the program changes."""
        self._compute_program_hash()
    
    def _initialize_log_file(self):
        """Create log file with headers if it doesn't exist."""
        try:
            from gbebox.storage import sd
            if sd.mount():
                if self.log_file_path.split('/')[-1] not in uos.listdir('/sd'):
                    with open(self.log_file_path, 'w') as file:
                        file.write(self.log_headers)
        except Exception as e:
            print(f"Error initializing log file: {e}")
            from gbebox.storage import sd
            uos.umount('/sd')
            sd.mount()
    
    async def start_logging(self):
        """Start the logging loop."""
        while True:
            await asyncio.sleep(self.interval)
            
            # Force garbage collection before data collection
            import gc
            gc.collect()
            
            sensor_data = self._collect_sensor_data()
            await self._log_to_sd(sensor_data)
            await self._upload_to_cloud(sensor_data)
    
    def _collect_sensor_data(self):
        """Collect all sensor data with timestamp."""
        from gbebox.sensors import sensor
        from gbebox.clock import clock
        
        sensor_data = sensor.all
        
        # Add timestamp using proper local time calculation
        # This ensures the log shows the correct local time regardless of timezone changes
        local_datetime = clock.get_local_datetime_from_utc()
        year, month, day, hour, minute, second = local_datetime
        
        sensor_data['Date'] = f'{year:04d}-{month:02d}-{day:02d}'
        sensor_data['Time'] = f'{hour:02d}:{minute:02d}:{second:02d}'
        
        return sensor_data
    
    async def _log_to_sd(self, sensor_data):
        """Log data to SD card."""
        # More memory-efficient CSV construction
        csv_parts = [
            str(sensor_data.get('Date', '')),
            str(sensor_data.get('Time', '')),
            str(sensor_data.get('Temperature (C)', '')),
            str(sensor_data.get('Humidity (%)', '')),
            str(sensor_data.get('CO2 (ppm)', '')),
            str(sensor_data.get('Pressure (Pa)', '')),
            str(sensor_data.get('Lux (lx)', '')),
            str(sensor_data.get('Voltage (V)', '')),
            str(sensor_data.get('Current (mA)', '')),
            str(sensor_data.get('Power (W)', '')),
            str(sensor_data.get('Fan Speed (rpm)', '')),
            str(sensor_data.get('Moisture', ''))
        ]
        csv_row = ','.join(csv_parts) + '\n'
        
        try:
            from gbebox.storage import sd
            if sd.mount():
                try:
                    with open(self.log_file_path, 'a') as file:
                        file.write(csv_row)
                    print("Logged sensor data:", sensor_data)
                except OSError as e:
                    # Handle specific SD card I/O errors - might be corruption or removal during write
                    print(f"SD card I/O error during write: {e}")
                    print("SD card may have been removed during write, will retry on next log cycle")
                except Exception as e:
                    print(f"Unexpected error writing to SD card: {e}")
            else:
                if sd.is_present():
                    print("SD card present but mount failed. Will retry on next log cycle.")
                else:
                    print("No SD card inserted. Skipping local logging.")
        except Exception as e:
            print(f"Error in SD card logging: {e}")
    
    async def _upload_to_cloud(self, sensor_data):
        """Upload data to cloud and handle program updates."""
        try:
            from gbebox.networking import wlan
            from gbebox.hardware import board
            from gbebox.sensors import sensor
            
            if not wlan.isconnected():
                print("Wi-Fi not connected. Skipping upload.")
                return
            
            # Add system info to data
            sensor_data['ID'] = board['id']
            
            # Add software and hardware dates for cloud server tracking
            import gbebox
            sensor_data['software_date'] = gbebox.software_date
            sensor_data['hardware_date'] = gbebox.hardware_date
            
            # Add program hash if available
            if self._cached_prog_hash:
                sensor_data['prog_hash'] = self._cached_prog_hash
            
            # Add sensor serial if available
            if sensor.scd:
                try:
                    sensor_data['scd_serial'] = ''.join([
                        '{:02x}'.format(x) for x in sensor.scd.serial_number
                    ])
                except Exception:
                    pass
            
            # Filter out None values
            filtered_data = {k: v for k, v in sensor_data.items() if v is not None}
            
            # Upload data
            url = "http://growingbeyond.earth/log_json.php"
            json_data = json.dumps(filtered_data)
            
            response = None
            try:
                # Force garbage collection before upload
                import gc
                gc.collect()
                free_memory = gc.mem_free()
                if free_memory < 30000:
                    print(f"Skipping cloud upload due to low memory: {free_memory} bytes free")
                    return
                
                headers = {"Content-Type": "application/json"}
                response = urequests.post(url, data=json_data, headers=headers, timeout=4)
                print("Upload response:", response.text)
                
                # Handle server responses
                await self._handle_server_response(response)
                
            finally:
                if response:
                    response.close()
                
                # Clean up variables and force garbage collection
                del json_data, filtered_data
                gc.collect()
            
        except Exception as e:
            print(f"Error uploading data to cloud: {e}")
            import gc
            gc.collect()
    
    async def _handle_server_response(self, response):
        """Handle server response for program updates."""
        try:
            response_data = response.json()
            
            # Check for program replacement
            if "program_replacement" in response_data:
                await self._handle_program_replacement(response_data["program_replacement"])
            
            # Check for hash mismatch
            if "prog_hash mismatch" in response.text:
                await self._upload_program_json()
        
        except Exception as e:
            print(f"Error handling server response: {e}")
    
    async def _handle_program_replacement(self, new_program):
        """Handle program replacement from server."""
        from gbebox.storage import sd
        
        print("Program replacement detected, updating...")
        
        try:
            if sd.save_program(new_program):
                print("New program loaded and saved to SD card.")
                # The program will be reloaded on next execution cycle
            else:
                print("Failed to save new program to SD card.")
        except Exception as e:
            print(f"Error handling program replacement: {e}")
    
    async def _upload_program_json(self):
        """Upload current program JSON to server."""
        try:
            from gbebox.hardware import board
            
            if not self.program_engine.program_json:
                return
            
            prog_hash = self._cached_prog_hash or ""
            
            upload_data = {
                'ID': board['id'],
                'prog_json': self.program_engine.program_json,
                'prog_hash': prog_hash
            }
            
            url = "http://growingbeyond.earth/prog.php"
            json_data = json.dumps(upload_data)
            
            response = urequests.post(url, data=json_data, 
                                    headers={"Content-Type": "application/json"}, 
                                    timeout=4)
            
            print("Program upload response:", response.text)
            response.close()
            
        except Exception as e:
            print(f"Error uploading program JSON: {e}")


# For backward compatibility, create a Run class that wraps ProgramEngine
class Run(ProgramEngine):
    """Backward compatibility wrapper for ProgramEngine."""
    
    def __init__(self, log_interval=600, sensor_check_interval=60):
        super().__init__(log_interval, sensor_check_interval)
    
    async def program(self):
        """Backward compatibility method."""
        return await self.run()