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

    def __init__(self, i2c_bus: I2C, addr: int = 0x40) -> None:
        self.i2c_bus = i2c_bus
        self.i2c_addr = addr
        self._cal_value = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_32V_2_5A()

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
        if corrected_value < 10: corrected_value = 0
        return corrected_value

    @property
    def power(self) -> float:
        self._write_register(_REG_CALIBRATION, self._cal_value)
        raw_value = self._read_register(_REG_POWER)
        corrected_value =  raw_value * self._power_lsb
        if corrected_value < 1: corrected_value = 0
        return corrected_value

    def set_calibration_32V_2_5A(self) -> None:
        self._current_lsb = 1.0  # Adjusted for accurate current reading
        self._cal_value = 4096
        self._power_lsb = 0.02  # Adjusted for accurate power reading
        self._write_register(_REG_CALIBRATION, self._cal_value)
        config = (BusVoltageRange.RANGE_32V << 13) | (Gain.DIV_8_320MV << 11) | \
                 (ADCResolution.ADCRES_12BIT_128S << 7) | (ADCResolution.ADCRES_12BIT_128S << 3) | Mode.SANDBVOLT_CONTINUOUS
        self._write_register(_REG_CONFIG, config)
