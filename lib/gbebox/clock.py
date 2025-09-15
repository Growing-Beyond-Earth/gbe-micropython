"""
Clock and time synchronization for GBE Box.

Handles RTC synchronization, NTP updates, and timezone management.
"""

import machine
import time
import uasyncio as asyncio
import ntptime
from .hardware import board, i2c0
from application.utils import calc


class ClockManager:
    """
    Real-time clock management with NTP and I2C RTC synchronization.
    
    Addresses the original static method inconsistencies with a proper
    instance-based API design.
    """
    
    def __init__(self):
        # Try to initialize I2C RTC
        self._i2c_rtc = None
        self._is_set = False
        self._ntp_synced = False
        self._i2c_rtc_available = False
        
        self._initialize_rtc()
    
    def _initialize_rtc(self):
        """Initialize the I2C RTC if available."""
        try:
            # Try to import and initialize DS3231
            ds3231_module = __import__('drivers.ds3231')
            ds3231 = getattr(ds3231_module, 'ds3231')
            self._i2c_rtc = ds3231.DS3231(i2c0)
            self._i2c_rtc_available = True
        except (ImportError, Exception) as e:
            print(f"I2C RTC not available: {e}")
            self._i2c_rtc = None
            self._i2c_rtc_available = False
    
    def sync_rtc_from_utc(self, utc_offset=0):
        """
        Sync MCU (local time) from I2C RTC (UTC time).
        
        Converts UTC time from I2C RTC to local time for MCU.
        
        Args:
            utc_offset: UTC offset in seconds
            
        Returns:
            bool: True if synchronization successful
        """
        if not self._i2c_rtc_available:
            return False
        
        try:
            # Get UTC time from I2C RTC
            utc_time = [x for x in self._i2c_rtc.DateTime()]
            
            # Convert to timestamp and add offset for local time
            utc_timestamp = time.mktime(tuple(utc_time[:6]) + (0, 0))
            local_timestamp = utc_timestamp + utc_offset
            local_time = time.localtime(local_timestamp)
            
            # Set MCU to local time
            local_rtc_time = [
                local_time[0], local_time[1], local_time[2], local_time[6],
                local_time[3], local_time[4], local_time[5], 0
            ]
            machine.RTC().datetime(local_rtc_time)
            return True
        except Exception as e:
            print(f"RTC sync from UTC error: {e}")
            return False
    
    def sync_rtc_to_utc(self, utc_offset=0):
        """
        Sync I2C RTC (UTC time) from MCU (local time).
        
        Converts local time from MCU to UTC time for I2C RTC.
        
        Args:
            utc_offset: UTC offset in seconds
            
        Returns:
            bool: True if synchronization successful
        """
        if not self._i2c_rtc_available:
            return False
        
        try:
            # Get local time from MCU
            mcu_time = machine.RTC().datetime()
            
            # Convert to timestamp and subtract offset to get UTC
            local_timestamp = time.mktime(tuple(mcu_time[:6]) + (0, 0))
            utc_timestamp = local_timestamp - utc_offset
            utc_time = time.localtime(utc_timestamp)
            
            # Set I2C RTC to UTC time
            utc_rtc_time = [
                utc_time[0], utc_time[1], utc_time[2], utc_time[6],
                utc_time[3], utc_time[4], utc_time[5], 0
            ]
            self._i2c_rtc.DateTime(utc_rtc_time[:8])
            return True
        except Exception as e:
            print(f"RTC sync to UTC error: {e}")
            return False
    
    def ntp_sync(self, utc_offset=0):
        """
        Synchronize clocks using NTP.
        
        Sets both MCU (local time) and I2C RTC (UTC time) from NTP.
        
        Args:
            utc_offset: UTC offset in seconds (from calc.to_seconds format)
            
        Returns:
            bool: True if NTP sync successful
        """
        # Check if WiFi is connected before attempting NTP sync
        from .networking import wlan
        if not wlan.isconnected():
            return False
            
        try:
            # Get UTC time from NTP
            ntptime.settime()  # This sets system time to UTC
            utc_timestamp = time.time()
            utc_time = time.localtime(utc_timestamp)
            
            # Set I2C RTC to UTC time
            if self._i2c_rtc_available:
                utc_rtc_time = [
                    utc_time[0], utc_time[1], utc_time[2], utc_time[6],
                    utc_time[3], utc_time[4], utc_time[5], 0
                ]
                self._i2c_rtc.DateTime(utc_rtc_time[:8])
            
            # Set MCU to local time
            local_timestamp = utc_timestamp + utc_offset
            local_time = time.localtime(local_timestamp)
            local_rtc_time = [
                local_time[0], local_time[1], local_time[2], local_time[6],
                local_time[3], local_time[4], local_time[5], 0
            ]
            machine.RTC().datetime(local_rtc_time)
            
            self._ntp_synced = True
            print(f"NTP sync successful - MCU: Local time, I2C RTC: UTC")
            return True
        except Exception as e:
            print(f"NTP sync error: {e}")
            return False
    
    def set_time(self, utc_offset=0):
        """
        Set system time using the best available source.
        
        New architecture:
        - I2C RTC always stores UTC time
        - MCU always stores local time
        - Priority: NTP -> I2C RTC (UTC) -> current MCU time
        
        Args:
            utc_offset: UTC offset in seconds
            
        Returns:
            bool: True if time was set successfully
        """
        # Try NTP first (sets both MCU local and I2C UTC)
        self._ntp_synced = self.ntp_sync(utc_offset)
        
        if self._ntp_synced:
            self._is_set = True
        else:
            # If NTP failed, try I2C RTC (assuming it has UTC time)
            current_rtc = machine.RTC().datetime()
            if current_rtc[0] == board.get("default_year", 2021):
                # MCU time is at default, sync from I2C RTC (UTC -> Local)
                self._is_set = self.sync_rtc_from_utc(utc_offset)
                print("Time set from I2C RTC (UTC) to MCU (local)")
            else:
                # MCU has valid local time, update I2C RTC with UTC
                self._is_set = True
                success = self.sync_rtc_to_utc(utc_offset)
                if success:
                    print("I2C RTC updated with UTC time from MCU (local)")
                else:
                    print("MCU time valid but I2C RTC update failed")
        
        return self._is_set
    
    async def setdaily(self, utc_offset=None):
        """
        Set time daily using configured timezone offset (backward compatibility name).
        
        Args:
            utc_offset: UTC offset in seconds, or None to use config
        """
        while True:
            if utc_offset is None:
                # Import here to avoid circular dependency
                from .storage import sd
                timezone_config = sd.tz_file
                if timezone_config:
                    offset_str = timezone_config.get("time zone", {}).get("UTC offset", "0")
                    utc_offset = calc.to_seconds(offset_str)
                else:
                    utc_offset = 0
            
            self.set_time(utc_offset)
            await asyncio.sleep(86400)  # 24 hours
    
    async def set_daily(self, utc_offset=None):
        """
        Set time daily using configured timezone offset.
        
        Args:
            utc_offset: UTC offset in seconds, or None to use config
        """
        return await self.setdaily(utc_offset)
    
    def get_current_date(self):
        """Get current date as (year, month, day) tuple."""
        dt = machine.RTC().datetime()
        return (dt[0], dt[1], dt[2])
    
    def get_current_time(self):
        """Get current time as (hour, minute, second) tuple."""
        dt = machine.RTC().datetime()
        return (dt[4], dt[5], dt[6])
    
    def get_current_datetime(self):
        """Get current date and time as (year, month, day, hour, minute, second) tuple."""
        dt = machine.RTC().datetime()
        return (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6])
    
    def get_utc_offset(self):
        """Get the current UTC offset in seconds from timezone configuration."""
        from .storage import sd
        timezone_config = sd.tz_file
        if timezone_config:
            offset_str = timezone_config.get("time zone", {}).get("UTC offset", "0")
            from application.utils import calc
            return calc.to_seconds(offset_str)
        return 0
    
    def get_utc_datetime(self):
        """
        Get current UTC time from I2C RTC.
        
        Returns:
            tuple: (year, month, day, hour, minute, second) in UTC, or None if not available
        """
        if not self._i2c_rtc_available:
            # Fall back to MCU time minus offset
            offset = self.get_utc_offset()
            mcu_time = machine.RTC().datetime()
            local_timestamp = time.mktime(tuple(mcu_time[:6]) + (0, 0))
            utc_timestamp = local_timestamp - offset
            utc_time = time.localtime(utc_timestamp)
            return (utc_time[0], utc_time[1], utc_time[2], utc_time[3], utc_time[4], utc_time[5])
        
        try:
            utc_time = [x for x in self._i2c_rtc.DateTime()]
            return (utc_time[0], utc_time[1], utc_time[2], utc_time[4], utc_time[5], utc_time[6])
        except Exception as e:
            print(f"Error reading UTC time from I2C RTC: {e}")
            return None
    
    def get_local_datetime_from_utc(self, utc_datetime=None):
        """
        Convert UTC time to local time using timezone offset.
        
        Args:
            utc_datetime: UTC datetime tuple, or None to use current UTC time
            
        Returns:
            tuple: (year, month, day, hour, minute, second) in local time
        """
        if utc_datetime is None:
            utc_datetime = self.get_utc_datetime()
        
        if utc_datetime is None:
            # Fallback to MCU time (already local)
            return self.get_current_datetime()
        
        utc_timestamp = time.mktime(tuple(utc_datetime[:6]) + (0, 0))
        offset = self.get_utc_offset()
        local_timestamp = utc_timestamp + offset
        local_time = time.localtime(local_timestamp)
        return (local_time[0], local_time[1], local_time[2], local_time[3], local_time[4], local_time[5])
    
    
    @property
    def is_set(self):
        """Check if clock has been set (not at default time)."""
        return self._is_set
    
    @property
    def ntp_synced(self):
        """Check if last sync was via NTP."""
        return self._ntp_synced
    
    @property
    def i2c_rtc_available(self):
        """Check if I2C RTC is available."""
        return self._i2c_rtc_available


# Create global instance
clock = ClockManager()