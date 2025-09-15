# MicroPython SCD4X Driver
# ========================
#
# This MicroPython driver for the Sensirion SCD4X CO2 sensor is adapted from the
# original CircuitPython driver created by Adafruit Industries.
#
# Original CircuitPython Driver:
# https://github.com/adafruit/Adafruit_CircuitPython_SCD4X
#
# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT
#
# This adaptation was done for compatibility with MicroPython, enabling use
# on platforms like the Raspberry Pi Pico W. The conversion process involved
# modifications to the I2C communication handling and other adjustments specific
# to the MicroPython environment.
#
# Sensor auto-calibration is disabled by default
#
# Adapted by: Growing Beyond Earth / Fairchild Tropical Botanic Garden
# Date: 25 August 2024


import time
from machine import I2C
from micropython import const

SCD4X_DEFAULT_ADDR = const(0x62)
_SCD4X_REINIT = const(0x3646)
_SCD4X_FACTORYRESET = const(0x3632)
_SCD4X_FORCEDRECAL = const(0x362F)
_SCD4X_SELFTEST = const(0x3639)
_SCD4X_DATAREADY = const(0xE4B8)
_SCD4X_STOPPERIODICMEASUREMENT = const(0x3F86)
_SCD4X_STARTPERIODICMEASUREMENT = const(0x21B1)
_SCD4X_STARTLOWPOWERPERIODICMEASUREMENT = const(0x21AC)
_SCD4X_READMEASUREMENT = const(0xEC05)
_SCD4X_SERIALNUMBER = const(0x3682)
_SCD4X_GETTEMPOFFSET = const(0x2318)
_SCD4X_SETTEMPOFFSET = const(0x241D)
_SCD4X_GETALTITUDE = const(0x2322)
_SCD4X_SETALTITUDE = const(0x2427)
_SCD4X_SETPRESSURE = const(0xE000)
_SCD4X_PERSISTSETTINGS = const(0x3615)
_SCD4X_GETASCE = const(0x2313)
_SCD4X_SETASCE = const(0x2416)
_SCD4X_MEASURESINGLESHOT = const(0x219D)
_SCD4X_MEASURESINGLESHOTRHTONLY = const(0x2196)


class SCD4X:
    def __init__(self, i2c_bus: I2C, address: int = SCD4X_DEFAULT_ADDR) -> None:
        self.i2c = i2c_bus
        self.address = address
        self._buffer = bytearray(18)
        self._cmd = bytearray(2)
        self._crc_buffer = bytearray(2)

        # Cached readings
        self._temperature = None
        self._relative_humidity = None
        self._co2 = None

        # Initialize the sensor
        self.stop_periodic_measurement()

        # Disable auto-calibration by default
        self.self_calibration_enabled = False

    @property
    def CO2(self) -> int:
        if self.data_ready:
            self._read_data()
        return self._co2

    @property
    def temperature(self) -> float:
        if self.data_ready:
            self._read_data()
        return self._temperature

    @property
    def relative_humidity(self) -> float:
        if self.data_ready:
            self._read_data()
        return self._relative_humidity

    def measure_single_shot(self) -> None:
        self._send_command(_SCD4X_MEASURESINGLESHOT, cmd_delay=5)

    def measure_single_shot_rht_only(self) -> None:
        self._send_command(_SCD4X_MEASURESINGLESHOTRHTONLY, cmd_delay=0.05)

    def reinit(self) -> None:
        self.stop_periodic_measurement()
        self._send_command(_SCD4X_REINIT, cmd_delay=0.02)

    def factory_reset(self) -> None:
        self.stop_periodic_measurement()
        self._send_command(_SCD4X_FACTORYRESET, cmd_delay=1.2)

    def force_calibration(self, target_co2: int) -> None:
        self.stop_periodic_measurement()
        self._set_command_value(_SCD4X_FORCEDRECAL, target_co2)
        time.sleep(0.5)
        self._read_reply(self._buffer, 3)
        correction = (self._buffer[0] << 8) | self._buffer[1]
        if correction == 0xFFFF:
            raise RuntimeError(
                "Forced recalibration failed. Make sure sensor is active for 3 minutes first"
            )

    @property
    def self_calibration_enabled(self) -> bool:
        self._send_command(_SCD4X_GETASCE, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return self._buffer[1] == 1

    @self_calibration_enabled.setter
    def self_calibration_enabled(self, enabled: bool) -> None:
        self._set_command_value(_SCD4X_SETASCE, 1 if enabled else 0)
        time.sleep(0.5)  # Ensure the sensor has time to process this change

    def self_test(self) -> None:
        self.stop_periodic_measurement()
        self._send_command(_SCD4X_SELFTEST, cmd_delay=10)
        self._read_reply(self._buffer, 3)
        if self._buffer[0] != 0 or self._buffer[1] != 0:
            raise RuntimeError("Self test failed")

    def _read_data(self) -> None:
        self._send_command(_SCD4X_READMEASUREMENT, cmd_delay=0.001)
        self._read_reply(self._buffer, 9)
        self._co2 = (self._buffer[0] << 8) | self._buffer[1]
        temp = (self._buffer[3] << 8) | self._buffer[4]
        self._temperature = -45 + 175 * (temp / 65535)
        humi = (self._buffer[6] << 8) | self._buffer[7]
        self._relative_humidity = 100 * (humi / 65535)

    @property
    def data_ready(self) -> bool:
        self._send_command(_SCD4X_DATAREADY, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return not ((self._buffer[0] & 0x07 == 0) and (self._buffer[1] == 0))

    @property
    def serial_number(self):
        self._send_command(_SCD4X_SERIALNUMBER, cmd_delay=0.001)
        self._read_reply(self._buffer, 9)
        return (
            self._buffer[0],
            self._buffer[1],
            self._buffer[3],
            self._buffer[4],
            self._buffer[6],
            self._buffer[7],
        )

    def stop_periodic_measurement(self) -> None:
        self._send_command(_SCD4X_STOPPERIODICMEASUREMENT, cmd_delay=0.5)

    def start_periodic_measurement(self) -> None:
        self._send_command(_SCD4X_STARTPERIODICMEASUREMENT)

    def start_low_periodic_measurement(self) -> None:
        self._send_command(_SCD4X_STARTLOWPOWERPERIODICMEASUREMENT)

    def persist_settings(self) -> None:
        self._send_command(_SCD4X_PERSISTSETTINGS, cmd_delay=0.8)

    def set_ambient_pressure(self, ambient_pressure: int) -> None:
        if ambient_pressure < 0 or ambient_pressure > 65535:
            raise AttributeError("`ambient_pressure` must be from 0~65535 hPascals")
        self._set_command_value(_SCD4X_SETPRESSURE, ambient_pressure)

    @property
    def temperature_offset(self) -> float:
        self._send_command(_SCD4X_GETTEMPOFFSET, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        temp = (self._buffer[0] << 8) | self._buffer[1]
        return temp * 175.0 / 65535

    @temperature_offset.setter
    def temperature_offset(self, offset: float) -> None:
        if offset > 374:
            raise AttributeError("Offset value must be less than or equal to 374 degrees Celsius")
        temp = int(offset * 65535 / 175)
        self._set_command_value(_SCD4X_SETTEMPOFFSET, temp)

    @property
    def altitude(self) -> int:
        self._send_command(_SCD4X_GETALTITUDE, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return (self._buffer[0] << 8) | self._buffer[1]

    @altitude.setter
    def altitude(self, height: int) -> None:
        if height > 65535:
            raise AttributeError("Height must be less than or equal to 65535 meters")
        self._set_command_value(_SCD4X_SETALTITUDE, height)

    def _check_buffer_crc(self, buf: bytearray) -> bool:
        for i in range(0, len(buf), 3):
            self._crc_buffer[0] = buf[i]
            self._crc_buffer[1] = buf[i + 1]
            if self._crc8(self._crc_buffer) != buf[i + 2]:
                raise RuntimeError("CRC check failed while reading data")
        return True

    def _send_command(self, cmd: int, cmd_delay: float = 0) -> None:
        self._cmd[0] = (cmd >> 8) & 0xFF
        self._cmd[1] = cmd & 0xFF

        try:
            self.i2c.writeto(self.address, self._cmd)
        except OSError as err:
            raise RuntimeError("I2C communication failed") from err
        time.sleep(cmd_delay)

    def _set_command_value(self, cmd, value, cmd_delay=0):
        self._buffer[0] = (cmd >> 8) & 0xFF
        self._buffer[1] = cmd & 0xFF
        self._crc_buffer[0] = self._buffer[2] = (value >> 8) & 0xFF
        self._crc_buffer[1] = self._buffer[3] = value & 0xFF
        self._buffer[4] = self._crc8(self._crc_buffer)
        self.i2c.writeto(self.address, self._buffer[:5])
        time.sleep(cmd_delay)

    def _read_reply(self, buff, num):
        self.i2c.readfrom_into(self.address, buff, num)
        self._check_buffer_crc(buff[:num])

    @staticmethod
    def _crc8(buffer: bytearray) -> int:
        crc = 0xFF
        for byte in buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF  # return the bottom 8 bits
