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
            from drivers.ds3231 import DS3231
            self._i2c_rtc = DS3231(i2c0)
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
            # I2C RTC format: (year, month, day, weekday, hour, minute, second, subsecond)

            # Extract components (skip weekday at position 3)
            year, month, day = utc_time[0], utc_time[1], utc_time[2]
            hour, minute, second = utc_time[4], utc_time[5], utc_time[6]

            # Convert to timestamp and add offset for local time
            # time.mktime expects: (year, month, day, hour, minute, second, weekday, yearday)
            utc_timestamp = time.mktime((year, month, day, hour, minute, second, 0, 0))
            local_timestamp = utc_timestamp + utc_offset
            local_time = time.localtime(local_timestamp)

            # Set MCU to local time
            # MCU RTC format: (year, month, day, weekday, hour, minute, second, subsecond)
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
            # MCU format: (year, month, day, weekday, hour, minute, second, subsecond)

            # Extract components (skip weekday at position 3)
            year, month, day = mcu_time[0], mcu_time[1], mcu_time[2]
            hour, minute, second = mcu_time[4], mcu_time[5], mcu_time[6]

            # Convert to timestamp and subtract offset to get UTC
            # time.mktime expects: (year, month, day, hour, minute, second, weekday, yearday)
            local_timestamp = time.mktime((year, month, day, hour, minute, second, 0, 0))
            utc_timestamp = local_timestamp - utc_offset
            utc_time = time.localtime(utc_timestamp)

            # Set I2C RTC to UTC time
            # I2C RTC format: (year, month, day, weekday, hour, minute, second, subsecond)
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
            
            # Format time strings for display
            utc_str = f"{utc_time[0]}-{utc_time[1]:02d}-{utc_time[2]:02d} {utc_time[3]:02d}:{utc_time[4]:02d}:{utc_time[5]:02d}"
            local_str = f"{local_time[0]}-{local_time[1]:02d}-{local_time[2]:02d} {local_time[3]:02d}:{local_time[4]:02d}:{local_time[5]:02d}"
            
            print(f"NTP sync successful - UTC: {utc_str}, Local: {local_str}")
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
        - Priority: Manual setting -> NTP -> I2C RTC (UTC) -> current MCU time

        Args:
            utc_offset: UTC offset in seconds

        Returns:
            bool: True if time was set successfully
        """
        # Check for manual time setting first
        date_str, time_str, utc_offset_hours = self._read_manual_time_setting()

        if date_str and time_str:
            # Manual time setting found
            print("Manual time setting found in set_clock.json")
            if self._apply_manual_time_setting(date_str, time_str, utc_offset_hours):
                self._clear_manual_time_setting()
                return True
            else:
                print("Manual time setting failed, falling back to automatic methods")
                self._clear_manual_time_setting()

        # Try NTP (sets both MCU local and I2C UTC)
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

                # Get times for display
                mcu_time = machine.RTC().datetime()
                # MCU format: (year, month, day, weekday, hour, minute, second, subsecond)
                year, month, day = mcu_time[0], mcu_time[1], mcu_time[2]
                hour, minute, second = mcu_time[4], mcu_time[5], mcu_time[6]

                local_timestamp = time.mktime((year, month, day, hour, minute, second, 0, 0))
                utc_timestamp = local_timestamp - utc_offset
                utc_time = time.localtime(utc_timestamp)

                local_str = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
                utc_str = f"{utc_time[0]}-{utc_time[1]:02d}-{utc_time[2]:02d} {utc_time[3]:02d}:{utc_time[4]:02d}:{utc_time[5]:02d}"

                success = self.sync_rtc_to_utc(utc_offset)
                if success:
                    print(f"I2C RTC updated with UTC time from MCU (local) - UTC: {utc_str}, Local: {local_str}")
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
            # MCU format: (year, month, day, weekday, hour, minute, second, subsecond)
            year, month, day = mcu_time[0], mcu_time[1], mcu_time[2]
            hour, minute, second = mcu_time[4], mcu_time[5], mcu_time[6]

            local_timestamp = time.mktime((year, month, day, hour, minute, second, 0, 0))
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

    def _read_manual_time_setting(self):
        """
        Read manual time setting from set_clock.json on SD card.

        Returns:
            tuple: (date_str, time_str, utc_offset_hours) or (None, None, None) if not set
        """
        try:
            from .storage import sd
            import json

            if not sd.mount():
                return None, None, None

            try:
                with open('/sd/set_clock.json', 'r') as f:
                    data = json.load(f)
            except OSError:
                # File doesn't exist on SD, try to copy from defaults
                try:
                    with open('/defaults/set_clock.json', 'r') as src:
                        content = src.read()
                    with open('/sd/set_clock.json', 'w') as dst:
                        dst.write(content)
                except:
                    pass
                return None, None, None

            date_str = data.get('date', '').strip()
            time_str = data.get('time', '').strip()
            utc_offset = data.get('utc_offset', '')

            # Check if values are actually set (not empty)
            if not date_str or not time_str:
                return None, None, None

            # Parse UTC offset if provided
            utc_offset_hours = None
            if utc_offset != '':
                try:
                    utc_offset_hours = float(utc_offset)
                except:
                    print(f"Invalid UTC offset in set_clock.json: {utc_offset}")

            return date_str, time_str, utc_offset_hours

        except Exception as e:
            print(f"Error reading set_clock.json: {e}")
            return None, None, None

    def _clear_manual_time_setting(self):
        """Clear the manual time settings in set_clock.json by restoring from defaults."""
        try:
            from .storage import sd

            if not sd.mount():
                return False

            try:
                # Copy the default template to SD card
                with open('/defaults/set_clock.json', 'r') as src:
                    content = src.read()
                with open('/sd/set_clock.json', 'w') as dst:
                    dst.write(content)

                return True
            except OSError:
                return False

        except Exception as e:
            print(f"Error clearing set_clock.json: {e}")
            return False

    def _apply_manual_time_setting(self, date_str, time_str, utc_offset_hours=None):
        """
        Apply manual time setting from user input.

        Args:
            date_str: Date string in YYYY-MM-DD format (local time)
            time_str: Time string in HH:MM:SS format (local time)
            utc_offset_hours: UTC offset in hours, or None to use existing timezone

        Returns:
            bool: True if successful
        """
        try:
            # Parse date and time
            date_parts = date_str.split('-')
            time_parts = time_str.split(':')

            if len(date_parts) != 3 or len(time_parts) != 3:
                print(f"Invalid date/time format in set_clock.json")
                return False

            year = int(date_parts[0])
            month = int(date_parts[1])
            day = int(date_parts[2])
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            second = int(time_parts[2])

            # Update timezone.json if UTC offset was provided
            if utc_offset_hours is not None:
                try:
                    from .storage import sd
                    import json

                    tz_data = {'time zone': {'UTC offset': utc_offset_hours}}

                    try:
                        from json_utils import jpretty
                        formatted_data = jpretty.jpretty(tz_data)
                    except ImportError:
                        formatted_data = json.dumps(tz_data, indent=2)

                    with open('/sd/timezone.json', 'w') as f:
                        f.write(formatted_data)

                    # Reload timezone config in storage manager
                    sd.load_settings()

                    print(f"Updated timezone to UTC{utc_offset_hours:+.1f}")
                except Exception as e:
                    print(f"Warning: Could not update timezone.json: {e}")

            # Get UTC offset in seconds
            utc_offset = calc.to_seconds(utc_offset_hours if utc_offset_hours is not None else self.get_utc_offset())

            # Set MCU to local time
            weekday = time.localtime(time.mktime((year, month, day, hour, minute, second, 0, 0)))[6]
            local_rtc_time = [year, month, day, weekday, hour, minute, second, 0]
            machine.RTC().datetime(local_rtc_time)

            # Set I2C RTC to UTC time
            if self._i2c_rtc_available:
                local_timestamp = time.mktime((year, month, day, hour, minute, second, 0, 0))
                utc_timestamp = local_timestamp - utc_offset
                utc_time = time.localtime(utc_timestamp)
                utc_rtc_time = [
                    utc_time[0], utc_time[1], utc_time[2], utc_time[6],
                    utc_time[3], utc_time[4], utc_time[5], 0
                ]
                self._i2c_rtc.DateTime(utc_rtc_time[:8])

            local_str = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
            print(f"Clock set manually to: {local_str} (local time)")

            self._is_set = True
            return True

        except Exception as e:
            print(f"Error applying manual time setting: {e}")
            return False


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