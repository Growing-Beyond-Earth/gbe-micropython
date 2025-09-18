"""
INA219 GBE MicroPython Library

This library provides a MicroPython driver for interfacing with the Texas Instruments INA219 current sensor, 
allowing for accurate measurement of voltage, current, and power in circuits. The INA219 is an essential component 
of the Growing Beyond Earth® (GBE) Control Box hardware, which monitors and manages power usage in various 
environmental control systems.

The code is adapted from Adafruit's CircuitPython INA219 library (https://github.com/adafruit/Adafruit_CircuitPython_INA219) 
and optimized for use in the GBE project.

Growing Beyond Earth® and this software are developed by Fairchild Tropical Botanic Garden, Miami, Florida, USA.

Date: September 14, 2024

For more information, visit: https://www.fairchildgarden.org/gbe
"""

from micropython import const
import ustruct
import json
from machine import I2C, Pin

# Bits
# pylint: disable=too-few-public-methods

# Config Register (R/W)
_REG_CONFIG = const(0x00)


class BusVoltageRange:
    """Constants for ``bus_voltage_range``"""
    RANGE_16V = 0x00  # set bus voltage range to 16V
    RANGE_32V = 0x01  # set bus voltage range to 32V (default)


class Gain:
    """Constants for ``gain``"""
    DIV_1_40MV = 0x00  # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV = 0x01  # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV = 0x02  # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV = 0x03  # shunt prog. gain set to /8, 320 mV range


class ADCResolution:
    """Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``"""
    ADCRES_9BIT_1S = 0x00  #  9bit,   1 sample,     84us
    ADCRES_10BIT_1S = 0x01  # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S = 0x02  # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S = 0x03  # 12 bit,  1 sample,    532us
    ADCRES_12BIT_2S = 0x09  # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S = 0x0A  # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S = 0x0B  # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S = 0x0C  # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S = 0x0D  # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S = 0x0E  # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S = 0x0F  # 12bit, 128 samples, 68.10ms


class Mode:
    """Constants for ``mode``"""
    POWERDOWN = 0x00  # power down
    SVOLT_TRIGGERED = 0x01  # shunt voltage triggered
    BVOLT_TRIGGERED = 0x02  # bus voltage triggered
    SANDBVOLT_TRIGGERED = 0x03  # shunt and bus voltage triggered
    ADCOFF = 0x04  # ADC off
    SVOLT_CONTINUOUS = 0x05  # shunt voltage continuous
    BVOLT_CONTINUOUS = 0x06  # bus voltage continuous
    SANDBVOLT_CONTINUOUS = 0x07  # shunt and bus voltage continuous


# SHUNT VOLTAGE REGISTER (R)
_REG_SHUNTVOLTAGE = const(0x01)

# BUS VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE = const(0x02)

# POWER REGISTER (R)
_REG_POWER = const(0x03)

# CURRENT REGISTER (R)
_REG_CURRENT = const(0x04)

# CALIBRATION REGISTER (R/W)
_REG_CALIBRATION = const(0x05)
# pylint: enable=too-few-public-methods


def _to_signed(num: int) -> int:
    if num > 0x7FFF:
        num -= 0x10000
    return num


class INA219:
    """Driver for the INA219 current sensor"""

    def __init__(self, i2c_bus: I2C, addr: int = 0x40, rsh_value: float = None) -> None:
        self.i2c_bus = i2c_bus
        self.i2c_addr = addr
        
        # Determine correct RSH value: check cache first, then use provided value, then default
        if rsh_value is None:
            self.rsh_value = self._get_cached_rsh_value()
        else:
            self.rsh_value = rsh_value
            
        self._cal_value = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_32V_2_5A()

    def _get_cached_rsh_value(self):
        """
        Get RSH value from cached hardware version detection.
        
        Returns:
            float: RSH value from cache, or default 0.0100 if cache not available
        """
        # RSH values by hardware version
        rsh_by_version = {
            "v1.5": 0.0100,
            "v1.4": 0.0136,
            "v1.0": 0.0109,
        }
        
        # Try to load cache file
        try:
            with open('/cache/hardware_version.json', 'r') as f:
                cache_data = json.load(f)
        except OSError:
            # File doesn't exist - this is normal on first boot
            # print("INA219: No hardware cache found, using default RSH")
            return 0.0100
        except ValueError:
            print("INA219: Cache file corrupted, using default RSH")
            return 0.0100
        
        # Check if we successfully loaded cache data
        if cache_data:
            # Only use cache if detection was successful
            detection_successful = cache_data.get('detection_successful', False)
            
            if detection_successful:
                version = cache_data.get('version')
                if version in rsh_by_version:
                    rsh_value = rsh_by_version[version]
                    # print(f"INA219: Using RSH={rsh_value} for {version}")
                    return rsh_value
                else:
                    print(f"INA219: Unknown version '{version}' in cache, using default")
            else:
                print("INA219: Previous detection failed, using default RSH")
            
        # Default to v1.5 value if no valid cache
        print("INA219: Using default RSH=0.0100")
        return 0.0100

    def _write_register(self, register: int, value: int) -> None:
        data = ustruct.pack(">H", value)
        self.i2c_bus.writeto_mem(self.i2c_addr, register, data)

    def _read_register(self, register: int) -> int:
        data = self.i2c_bus.readfrom_mem(self.i2c_addr, register, 2)
        return ustruct.unpack(">H", data)[0]

    @property
    def shunt_voltage(self) -> float:
        raw_value = self._read_register(_REG_SHUNTVOLTAGE)
        return _to_signed(raw_value) * 0.00001

    @property
    def bus_voltage(self) -> float:
        raw_value = self._read_register(_REG_BUSVOLTAGE) >> 3
        corrected_value = raw_value * 0.004
        if corrected_value < 2: corrected_value = 0
        return corrected_value

    @property
    def current(self) -> float:
        self._write_register(_REG_CALIBRATION, self._cal_value)
        raw_value = self._read_register(_REG_CURRENT)
        corrected_value = _to_signed(raw_value) * self._current_lsb
        # Convert to mA and apply threshold  
        corrected_value_ma = corrected_value * 1000
        if corrected_value_ma < 10: corrected_value_ma = 0
        return corrected_value_ma

    @property
    def power(self) -> float:
        self._write_register(_REG_CALIBRATION, self._cal_value)
        raw_value = self._read_register(_REG_POWER)
        corrected_value =  raw_value * self._power_lsb
        if corrected_value < 1: corrected_value = 0
        return corrected_value

    def set_calibration_32V_2_5A(self) -> None:
        # Calculate calibration values based on actual shunt resistor value
        # Formula: CAL = 0.04096 / (Current_LSB * R_shunt)
        # We want Current_LSB to give us good resolution for expected current range
        
        # Calculate Current_LSB based on expected current range and RSH value
        # For INA219, we want CAL to be in a reasonable range (avoid overflow)
        # CAL = 0.04096 / (Current_LSB * R_shunt)
        # Rearranging: Current_LSB = 0.04096 / (CAL * R_shunt)
        # We want CAL around 20000-30000 for good resolution
        
        target_cal = 25000  # Good middle value
        self._current_lsb = 0.04096 / (target_cal * self.rsh_value)
        
        # Now calculate actual CAL with this Current_LSB
        cal_float = 0.04096 / (self._current_lsb * self.rsh_value)
        self._cal_value = int(cal_float)
        
        # Power LSB is 20x Current LSB
        self._power_lsb = 20 * self._current_lsb
        
        self._write_register(_REG_CALIBRATION, self._cal_value)
        config = (BusVoltageRange.RANGE_32V << 13) | (Gain.DIV_8_320MV << 11) | \
                 (ADCResolution.ADCRES_12BIT_128S << 7) | (ADCResolution.ADCRES_12BIT_128S << 3) | Mode.SANDBVOLT_CONTINUOUS
        self._write_register(_REG_CONFIG, config)
