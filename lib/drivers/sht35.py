"""
SHT35 Temperature and Humidity Sensor Driver for MicroPython

This driver provides a MicroPython interface for the Sensirion SHT35
temperature and humidity sensor via I2C communication.

The SHT35 provides high-accuracy temperature (±0.1°C) and humidity (±1.5% RH)
measurements with excellent long-term stability.
"""

import time
import struct


class SHT35:
    """
    Driver for SHT35 temperature and humidity sensor.
    
    The SHT35 uses I2C communication and provides high-precision
    temperature and humidity measurements.
    """
    
    # Default I2C address
    DEFAULT_ADDRESS = 0x44
    
    # Command codes for different measurement modes
    # High repeatability, clock stretching disabled
    MEASURE_HIGH_REP_NO_STRETCH = 0x2400
    
    # Medium repeatability, clock stretching disabled  
    MEASURE_MED_REP_NO_STRETCH = 0x240B
    
    # Low repeatability, clock stretching disabled
    MEASURE_LOW_REP_NO_STRETCH = 0x2416
    
    # Soft reset command
    SOFT_RESET = 0x30A2
    
    # Status register read command
    READ_STATUS = 0xF32D
    
    def __init__(self, i2c, address=DEFAULT_ADDRESS):
        """
        Initialize the SHT35 sensor.
        
        Args:
            i2c: I2C bus object
            address: I2C address (default 0x44)
        """
        self.i2c = i2c
        self.address = address
        
        # Verify sensor is present and responding
        self._soft_reset()
        time.sleep_ms(10)  # Wait for reset to complete
        
        # Try to read status to verify communication
        try:
            self._read_status()
        except (OSError, RuntimeError) as e:
            raise RuntimeError(f"SHT35 sensor not found at address 0x{address:02X}: {e}")
    
    def _write_command(self, command):
        """Write a command to the sensor."""
        cmd_bytes = struct.pack('>H', command)
        self.i2c.writeto(self.address, cmd_bytes)
    
    def _read_data(self, num_bytes):
        """Read data from the sensor."""
        return self.i2c.readfrom(self.address, num_bytes)
    
    def _soft_reset(self):
        """Perform a soft reset of the sensor."""
        self._write_command(self.SOFT_RESET)
    
    def _read_status(self):
        """Read the status register."""
        self._write_command(self.READ_STATUS)
        time.sleep_ms(1)
        data = self._read_data(3)  # 2 bytes status + 1 byte CRC
        return struct.unpack('>H', data[:2])[0]
    
    def _crc8(self, data):
        """
        Calculate CRC8 checksum for data validation.
        
        SHT35 uses CRC8 with polynomial 0x31 (x^8 + x^5 + x^4 + 1)
        """
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF
    
    def _read_measurement(self, command=MEASURE_HIGH_REP_NO_STRETCH):
        """
        Read temperature and humidity measurement.
        
        Args:
            command: Measurement command (default high repeatability)
            
        Returns:
            tuple: (temperature_c, humidity_percent)
        """
        # Send measurement command
        self._write_command(command)
        
        # Wait for measurement to complete
        # High repeatability takes ~15ms, add some margin
        time.sleep_ms(20)
        
        # Read 6 bytes: temp_high, temp_low, temp_crc, hum_high, hum_low, hum_crc
        try:
            data = self._read_data(6)
        except OSError as e:
            raise RuntimeError(f"Failed to read measurement data: {e}")
        
        if len(data) != 6:
            raise RuntimeError(f"Expected 6 bytes, got {len(data)}")
        
        # Extract temperature data and CRC
        temp_data = data[0:2]
        temp_crc = data[2]
        
        # Extract humidity data and CRC  
        hum_data = data[3:5]
        hum_crc = data[5]
        
        # Verify CRC checksums
        if self._crc8(temp_data) != temp_crc:
            raise RuntimeError("Temperature CRC check failed")
        
        if self._crc8(hum_data) != hum_crc:
            raise RuntimeError("Humidity CRC check failed")
        
        # Convert raw values to temperature and humidity
        temp_raw = struct.unpack('>H', temp_data)[0]
        hum_raw = struct.unpack('>H', hum_data)[0]
        
        # Convert to physical values
        # Temperature: -45°C to +130°C mapped to 0x0000 to 0xFFFF
        temperature = -45 + (175 * temp_raw / 65535)
        
        # Humidity: 0% to 100% RH mapped to 0x0000 to 0xFFFF
        humidity = 100 * hum_raw / 65535
        
        # Clamp humidity to valid range
        humidity = max(0, min(100, humidity))
        
        return temperature, humidity
    
    @property
    def temperature(self):
        """Get temperature in degrees Celsius."""
        temp, _ = self._read_measurement()
        return temp
    
    @property
    def humidity(self):
        """Get relative humidity as percentage."""
        _, humidity = self._read_measurement()
        return humidity
    
    def read(self):
        """
        Read both temperature and humidity in one measurement.
        
        Returns:
            tuple: (temperature_c, humidity_percent)
        """
        return self._read_measurement()
    
    def reset(self):
        """Reset the sensor."""
        self._soft_reset()
        time.sleep_ms(10)