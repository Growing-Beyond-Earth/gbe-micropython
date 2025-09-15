"""
Sensor management for GBE Box.

Provides unified interface for all environmental sensors with consistent API design.
Addresses the static/instance method inconsistencies from the original design.
"""

import time
import uasyncio as asyncio
from .hardware import board, i2c0, i2c1


def load_libraries(library_names):
    """Dynamically load sensor libraries."""
    loaded = {}
    for name in library_names:
        try:
            if '.' in name:
                # Handle dotted imports like 'drivers.mpl3115a2'
                module = __import__(name)
                # Navigate to the actual submodule
                for attr in name.split('.')[1:]:
                    module = getattr(module, attr)
                loaded[name] = module
            else:
                loaded[name] = __import__(name)
        except ImportError as e:
            loaded[name] = None
            print(f"{name} library not found or failed to load: {e}")
        except Exception as e:
            loaded[name] = None
            print(f"{name} library failed to load due to error: {e}")
    return loaded


# Load sensor libraries from drivers directory
sensor_libs = load_libraries([
    "drivers.scd4x", "drivers.mpl3115a2", "drivers.ina219_gbe", "drivers.veml7700", 
    "drivers.ds3231", "drivers.seesaw", "drivers.stemma_soil_sensor", "drivers.fan_rpm", "drivers.sht35"
])


class SensorReading:
    """Simple sensor reading with retry capability."""
    
    def __init__(self, value_func=None, unit="Unknown unit", device="Unknown device", retries=2):
        self.value_func = value_func
        self._unit = unit
        self._device = device
        self._retries = retries

    def __call__(self):
        """Get the current sensor value with retry mechanism."""
        if not self.value_func:
            return None
        
        for attempt in range(self._retries + 1):
            try:
                return self.value_func()
            except (RuntimeError, OSError) as e:
                if attempt < self._retries:
                    time.sleep_ms(50)  # Small delay before retry
                    continue
                else:
                    print(f"I2C communication error reading sensor {self._device}: {e}")
                    return None
            except Exception as e:
                print(f"Unexpected error reading sensor {self._device}: {e}")
                return None
        
        return None

    @property
    def unit(self):
        return self._unit

    @property
    def device(self):
        return self._device


class SensorManager:
    """
    Unified sensor management class.
    
    This class addresses the static/instance method inconsistencies by making
    all sensor operations instance-based with clear initialization.
    """
    
    def __init__(self):
        self._sensors = {}
        self._last_i2c1_scan = []  # Track detected I2C1 devices for hot-plug detection
        self._initialize_sensors()
    
    def _initialize_sensor(self, module_name, sensor_class_name, *args, **kwargs):
        """Initialize a sensor if its module is available."""
        module = sensor_libs.get(module_name)
        if module:
            try:
                sensor_class = getattr(module, sensor_class_name)
                return sensor_class(*args, **kwargs)
            except Exception:
                return None
        else:
            return None
    
    def _initialize_sensors(self):
        """Initialize all available sensors."""
        # Power monitoring
        self._sensors['ina'] = self._initialize_sensor('drivers.ina219_gbe', 'INA219', i2c0)
        
        # Environmental sensors (all on I2C1 - optional accessories)
        self._sensors['veml'] = self._initialize_sensor('drivers.veml7700', 'VEML7700', 
                                                       address=0x10, i2c=i2c1, it=100, gain=1/8)
        self._sensors['mpl'] = self._initialize_sensor('drivers.mpl3115a2', 'MPL3115A2', 
                                                      i2c1, mode=sensor_libs['drivers.mpl3115a2'].MPL3115A2.PRESSURE if sensor_libs['drivers.mpl3115a2'] else None)
        self._sensors['seesaw'] = self._initialize_sensor('drivers.stemma_soil_sensor', 'StemmaSoilSensor', i2c1)
        
        # High-precision temperature and humidity sensor (SHT35)
        self._sensors['sht35'] = self._initialize_sensor('drivers.sht35', 'SHT35', i2c1, address=0x44)
        
        # Fan RPM (special case - not from a library module)
        if sensor_libs['drivers.fan_rpm']:
            self._sensors['rpm'] = sensor_libs['drivers.fan_rpm'].FanRPM(pin_num=board["pins"]["rpm"])
        else:
            self._sensors['rpm'] = None
        
        # CO2/Temperature/Humidity sensor
        self._sensors['scd'] = self._initialize_sensor('drivers.scd4x', 'SCD4X', i2c1)
        if self._sensors['scd']:
            self._sensors['scd'].temperature_offset = 0
            if self._sensors['mpl']:
                self._sensors['scd'].set_ambient_pressure(round(self._sensors['mpl'].pressure() / 100))
            self._sensors['scd'].start_periodic_measurement()
    
    def reinitialize_scd4x_if_needed(self):
        """Reinitialize the SCD4x sensor if it's not responding."""
        scd = self._sensors.get('scd')
        if not scd:
            return
        
        try:
            # Quick health check
            test_reading = scd.CO2
            if test_reading is not None:
                return  # Sensor is working fine
        except (RuntimeError, OSError):
            pass  # Continue to reinitialization
        
        try:
            print("SCD4x sensor not responding, reinitializing...")
            scd.reinit()
            time.sleep(2)
            scd.temperature_offset = 0
            
            # Set ambient pressure if MPL sensor is available
            if self._sensors['mpl']:
                try:
                    pressure = self._sensors['mpl'].pressure()
                    if pressure is not None:
                        scd.set_ambient_pressure(round(pressure / 100))
                except (RuntimeError, OSError) as e:
                    print(f"Could not read pressure for SCD4x calibration: {e}")
            
            scd.start_periodic_measurement()
            print("SCD4x sensor reinitialization complete")
            
        except (RuntimeError, OSError) as e:
            print(f"SCD4x reinitialization failed: {e}")
    
    
    @property
    def temperature(self):
        """Get temperature reading from best available sensor."""
        # Priority: SHT35 (highest accuracy) > MPL3115A2 > SCD4x > Seesaw
        if self._sensors['sht35']:
            return SensorReading(lambda: round(self._sensors['sht35'].temperature, 1) if self._sensors['sht35'].temperature is not None else None, "C", "sht35")
        elif self._sensors['mpl']:
            return SensorReading(lambda: round(self._sensors['mpl'].temperature(), 1) if self._sensors['mpl'].temperature() is not None else None, "C", "mpl3115a2")
        elif self._sensors['scd']:
            return SensorReading(lambda: round(self._sensors['scd'].temperature, 1) if self._sensors['scd'].temperature is not None else None, "C", "scd4x")
        elif self._sensors['seesaw']:
            return SensorReading(lambda: round(self._sensors['seesaw'].get_temp(), 1) if self._sensors['seesaw'].get_temp() is not None else None, "C", "seesaw")
        return SensorReading()

    @property
    def humidity(self):
        """Get humidity reading."""
        # Priority: SHT35 (highest accuracy) > SCD4x
        if self._sensors['sht35']:
            return SensorReading(lambda: round(self._sensors['sht35'].humidity, 1) if self._sensors['sht35'].humidity is not None else None, "%", "sht35")
        elif self._sensors['scd']:
            return SensorReading(lambda: round(self._sensors['scd'].relative_humidity) if self._sensors['scd'].relative_humidity is not None else None, "%", "scd4x")
        return SensorReading()

    @property
    def co2(self):
        """Get CO2 reading."""
        if self._sensors['scd']:
            return SensorReading(lambda: self._sensors['scd'].CO2 if self._sensors['scd'].CO2 is not None else None, "ppm", "scd4x")
        return SensorReading()

    @property
    def pressure(self):
        """Get pressure reading."""
        if self._sensors['mpl']:
            return SensorReading(lambda: round(self._sensors['mpl'].pressure()) if self._sensors['mpl'].pressure() is not None else None, "Pa", "mpl3115a2")
        return SensorReading()

    @property
    def lux(self):
        """Get light level reading."""
        if self._sensors['veml']:
            return SensorReading(lambda: self._sensors['veml'].read_lux() if self._sensors['veml'].read_lux() is not None else None, "lx", "veml7700")
        return SensorReading()

    @property
    def voltage(self):
        """Get voltage reading."""
        if self._sensors['ina']:
            return SensorReading(lambda: round(self._sensors['ina'].bus_voltage, 1) if self._sensors['ina'].bus_voltage is not None else None, "V", "ina219")
        return SensorReading()

    @property
    def current(self):
        """Get current reading."""
        if self._sensors['ina']:
            return SensorReading(lambda: round(self._sensors['ina'].current) if self._sensors['ina'].current is not None else None, "mA", "ina219")
        return SensorReading()

    @property
    def power(self):
        """Get power reading."""
        if self._sensors['ina']:
            return SensorReading(lambda: round(self._sensors['ina'].power, 1) if self._sensors['ina'].power is not None else None, "W", "ina219")
        return SensorReading()

    @property
    def fan_speed(self):
        """Get fan speed reading."""
        if self._sensors['rpm']:
            return SensorReading(lambda: self._sensors['rpm'].get_rpm() if self._sensors['rpm'].get_rpm() is not None else None, "rpm", "fan_rpm")
        return SensorReading()

    @property
    def moisture(self):
        """Get moisture reading."""
        if self._sensors['seesaw']:
            return SensorReading(lambda: self._sensors['seesaw'].get_moisture() if self._sensors['seesaw'].get_moisture() is not None else None, None, "seesaw")
        return SensorReading()

    @property
    def all(self):
        """Get all sensor readings as a dictionary."""
        return {
            'Temperature (C)': self.temperature(),
            'Humidity (%)': self.humidity(),
            'CO2 (ppm)': self.co2(),
            'Pressure (Pa)': self.pressure(),
            'Lux (lx)': self.lux(),
            'Voltage (V)': self.voltage(),
            'Current (mA)': self.current(),
            'Power (W)': self.power(),
            'Fan Speed (rpm)': self.fan_speed(),
            'Moisture': self.moisture(),
        }
    
    def get_available_sensors(self):
        """Get list of available sensors."""
        available = []
        if self._sensors['ina']:
            available.append('INA219 (Voltage, Current, Power)')
        if self._sensors['veml']:
            available.append('VEML7700 (Lux)')
        if self._sensors['mpl']:
            available.append('MPL3115A2 (Pressure, Temperature)')
        if self._sensors['seesaw']:
            available.append('Seesaw (Moisture, Temperature)')
        if self._sensors['rpm']:
            available.append('FanRPM (Fan Speed)')
        if self._sensors['scd']:
            available.append('SCD4X (CO2, Temperature, Humidity)')
        if self._sensors['sht35']:
            available.append('SHT35 (Temperature, Humidity)')
        return available
    
    def scan_i2c1_bus(self):
        """Scan I2C1 bus for connected devices."""
        devices = []
        try:
            # Scan all possible I2C addresses (0x08 to 0x77)
            for addr in range(0x08, 0x78):
                try:
                    i2c1.writeto(addr, b'')  # Try to write empty byte
                    devices.append(addr)
                except OSError:
                    pass  # No device at this address
        except Exception as e:
            print(f"I2C1 scan error: {e}")
        
        return sorted(devices)
    
    def _detect_sensor_changes(self):
        """Detect if I2C1 sensors have changed."""
        current_scan = self.scan_i2c1_bus()
        
        if current_scan != self._last_i2c1_scan:
            added = set(current_scan) - set(self._last_i2c1_scan)
            removed = set(self._last_i2c1_scan) - set(current_scan)
            
            if added or removed:
                if added:
                    print(f"I2C1 devices added: {[hex(addr) for addr in added]}")
                if removed:
                    print(f"I2C1 devices removed: {[hex(addr) for addr in removed]}")
                
                self._last_i2c1_scan = current_scan
                return True
        
        return False
    
    def reload_i2c1_sensors(self):
        """Reload only I2C1 sensors while preserving I2C0 sensors."""
        print("Reloading I2C1 sensors...")
        
        # Store I2C0 sensors (power monitoring)
        ina_sensor = self._sensors.get('ina')
        rpm_sensor = self._sensors.get('rpm')
        
        # Clear I2C1 sensors
        i2c1_sensors = ['veml', 'mpl', 'seesaw', 'sht35', 'scd']
        for sensor_key in i2c1_sensors:
            self._sensors[sensor_key] = None
        
        # Reinitialize I2C1 sensors
        self._sensors['veml'] = self._initialize_sensor('drivers.veml7700', 'VEML7700', 
                                                       address=0x10, i2c=i2c1, it=100, gain=1/8)
        self._sensors['mpl'] = self._initialize_sensor('drivers.mpl3115a2', 'MPL3115A2', 
                                                      i2c1, mode=sensor_libs['drivers.mpl3115a2'].MPL3115A2.PRESSURE if sensor_libs['drivers.mpl3115a2'] else None)
        self._sensors['seesaw'] = self._initialize_sensor('drivers.stemma_soil_sensor', 'StemmaSoilSensor', i2c1)
        self._sensors['sht35'] = self._initialize_sensor('drivers.sht35', 'SHT35', i2c1, address=0x44)
        self._sensors['scd'] = self._initialize_sensor('drivers.scd4x', 'SCD4X', i2c1)
        
        # Restore I2C0 sensors
        self._sensors['ina'] = ina_sensor
        self._sensors['rpm'] = rpm_sensor
        
        # Configure SCD4x if available
        if self._sensors['scd']:
            self._sensors['scd'].temperature_offset = 0
            if self._sensors['mpl']:
                try:
                    pressure = self._sensors['mpl'].pressure()
                    if pressure is not None:
                        self._sensors['scd'].set_ambient_pressure(round(pressure / 100))
                except Exception:
                    pass
            self._sensors['scd'].start_periodic_measurement()
        
        # Update scan record
        self._last_i2c1_scan = self.scan_i2c1_bus()
        print("I2C1 sensor reload complete")
    
    async def monitor_sensor_changes(self, scan_interval=60):
        """Monitor I2C1 for sensor changes and reload when detected."""
        import uasyncio as asyncio
        
        print(f"Starting I2C1 sensor monitoring (scan interval: {scan_interval}s)")
        
        # Initial scan
        self._last_i2c1_scan = self.scan_i2c1_bus()
        
        while True:
            await asyncio.sleep(scan_interval)
            
            try:
                if self._detect_sensor_changes():
                    self.reload_i2c1_sensors()
                    
                    # Show updated sensor list
                    available = self.get_available_sensors()
                    if available:
                        print("Updated sensor list:")
                        for sensor_info in available:
                            print(f"  {sensor_info}")
                    
            except Exception as e:
                print(f"Error monitoring sensor changes: {e}")
    
    @property
    def scd(self):
        """Direct access to SCD4X sensor for advanced operations."""
        return self._sensors.get('scd')
    
    def cleanup(self):
        """Clean up sensor resources (memory management only - boot.py handles SCD4X)."""
        try:
            # Clear sensor references to help with garbage collection
            for sensor_name in self._sensors:
                self._sensors[sensor_name] = None
            
            # Force garbage collection
            import gc
            gc.collect()
            
            print("Sensor references cleared for garbage collection")
        except Exception as e:
            print(f"Error during sensor cleanup: {e}")
    
    def get_memory_usage(self):
        """Get current memory usage statistics."""
        import gc
        return {
            'free': gc.mem_free(),
            'allocated': gc.mem_alloc(),
            'sensor_count': len([s for s in self._sensors.values() if s is not None])
        }


# Create global sensor instance
sensor = SensorManager()