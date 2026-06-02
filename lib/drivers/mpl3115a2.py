import utime as time
from machine import I2C, Pin
from micropython import const

class MPL3115A2exception(Exception):
    pass

class MPL3115A2:
    ALTITUDE = const(0)
    PRESSURE = const(1)

    MPL3115_I2CADDR = const(0x60)
    MPL3115_STATUS = const(0x00)
    MPL3115_PRESSURE_DATA_MSB = const(0x01)
    MPL3115_PRESSURE_DATA_CSB = const(0x02)
    MPL3115_PRESSURE_DATA_LSB = const(0x03)
    MPL3115_TEMP_DATA_MSB = const(0x04)
    MPL3115_TEMP_DATA_LSB = const(0x05)
    MPL3115_DR_STATUS = const(0x06)
    MPL3115_DELTA_DATA = const(0x07)
    MPL3115_WHO_AM_I = const(0x0C)
    MPL3115_FIFO_STATUS = const(0x0D)
    MPL3115_FIFO_DATA = const(0x0E)
    MPL3115_FIFO_SETUP = const(0x0E)
    MPL3115_TIME_DELAY = const(0x10)
    MPL3115_SYS_MODE = const(0x11)
    MPL3115_INT_SORCE = const(0x12)
    MPL3115_PT_DATA_CFG = const(0x13)
    MPL3115_BAR_IN_MSB = const(0x14)
    MPL3115_P_ARLARM_MSB = const(0x16)
    MPL3115_T_ARLARM = const(0x18)
    MPL3115_P_ARLARM_WND_MSB = const(0x19)
    MPL3115_T_ARLARM_WND = const(0x1B)
    MPL3115_P_MIN_DATA = const(0x1C)
    MPL3115_T_MIN_DATA = const(0x1F)
    MPL3115_P_MAX_DATA = const(0x21)
    MPL3115_T_MAX_DATA = const(0x24)
    MPL3115_CTRL_REG1 = const(0x26)
    MPL3115_CTRL_REG2 = const(0x27)
    MPL3115_CTRL_REG3 = const(0x28)
    MPL3115_CTRL_REG4 = const(0x29)
    MPL3115_CTRL_REG5 = const(0x2A)
    MPL3115_OFFSET_P = const(0x2B)
    MPL3115_OFFSET_T = const(0x2C)
    MPL3115_OFFSET_H = const(0x2D)

    def __init__(self, i2c, mode=PRESSURE, status_timeout_ms=1200):
        self.i2c = i2c
        self.STA_reg = bytearray(1)
        self.mode = mode

        if self.mode == PRESSURE:
            self.i2c.writeto_mem(0x60, 0x26, bytes([0x38]))  # CTRL_REG1 standby
            self.i2c.writeto_mem(0x60, 0x13, bytes([0x07]))  # PT_DATA_CFG
            self.i2c.writeto_mem(0x60, 0x26, bytes([0x39]))  # active mode
        elif self.mode == ALTITUDE:
            self.i2c.writeto_mem(0x60, 0x26, bytes([0xB8]))  # CTRL_REG1 standby
            self.i2c.writeto_mem(0x60, 0x13, bytes([0x07]))  # PT_DATA_CFG
            self.i2c.writeto_mem(0x60, 0x26, bytes([0xB9]))  # active mode
        else:
            raise MPL3115A2exception("Invalid Mode MPL3115A2")

        # Wait (up to ~1.2 s) for the first sample to become ready,
        # but do not fail if it times out — later reads will succeed.
        self._read_status(timeout_ms=status_timeout_ms)

    def _read_status(self, timeout_ms=250):
        """
        Poll STATUS for data-ready (bit 2). Return True if ready before timeout,
        False if not ready. Tolerates transient I2C errors.
        """
        t0 = time.ticks_ms()
        while True:
            try:
                self.i2c.readfrom_mem_into(self.MPL3115_I2CADDR, self.MPL3115_STATUS, self.STA_reg)
                if self.STA_reg[0] & 0x04:  # data ready
                    return True
            except Exception:
                # ignore and retry until timeout
                pass
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_ms:
                return False
            time.sleep_ms(10)

    def pressure(self):
        if self.mode == self.ALTITUDE:
            raise MPL3115A2exception("Incorrect Measurement Mode MPL3115A2")
        out_pressure = self.i2c.readfrom_mem(self.MPL3115_I2CADDR, self.MPL3115_PRESSURE_DATA_MSB, 3)
        pressure_int = (out_pressure[0] << 10) + (out_pressure[1] << 2) + ((out_pressure[2] >> 6) & 0x3)
        pressure_frac = (out_pressure[2] >> 4) & 0x03
        return float(pressure_int + pressure_frac / 4.0)

    def altitude(self):
        if self.mode == self.PRESSURE:
            raise MPL3115A2exception("Incorrect Measurement Mode MPL3115A2")
        out_alt = self.i2c.readfrom_mem(self.MPL3115_I2CADDR, self.MPL3115_PRESSURE_DATA_MSB, 3)
        alt_int = (out_alt[0] << 8) + (out_alt[1])
        alt_frac = ((out_alt[2] >> 4) & 0x0F)
        if alt_int > 32767:
            alt_int -= 65536
        return float(alt_int + alt_frac / 16.0)

    def temperature(self):
        OUT_T_MSB = self.i2c.readfrom_mem(self.MPL3115_I2CADDR, self.MPL3115_TEMP_DATA_MSB, 1)
        OUT_T_LSB = self.i2c.readfrom_mem(self.MPL3115_I2CADDR, self.MPL3115_TEMP_DATA_LSB, 1)
        temp_int = OUT_T_MSB[0]
        temp_frac = OUT_T_LSB[0]
        if temp_int > 127:
            temp_int -= 256
        return float(temp_int + temp_frac / 256.0)
