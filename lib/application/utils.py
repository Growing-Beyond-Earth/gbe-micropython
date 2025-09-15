"""
Utility functions for GBE Box.

Common calculations and helper functions.
"""

import time
import sys
from io import StringIO


class TimeCalculator:
    """Utility functions for time calculations and conversions."""
    
    @staticmethod
    def to_seconds(input_time):
        """
        Convert time (string, integer, or float) to seconds.
        
        Supports formats:
        - "HH:MM:SS" 
        - "HH:MM"
        - Decimal hours (e.g., 1.5 for 1 hour 30 minutes)
        - Negative values supported
        """
        input_str = str(input_time)
        parts = input_str.split(':')
        
        if len(parts) == 3:
            # HH:MM:SS format
            hours, minutes, seconds = map(int, parts)
        elif len(parts) == 2:
            # HH:MM format
            hours, minutes = map(int, parts)
            seconds = 0
        elif len(parts) == 1:
            # Decimal hours format
            decimal_time = float(parts[0])
            hours = int(decimal_time)
            minutes = int((decimal_time - hours) * 60)
            seconds = 0
        else:
            raise ValueError(f"Invalid time format: {input_time}")
        
        total_seconds = abs((hours * 3600) + (minutes * 60) + seconds)
        
        # Handle negative values
        if input_str.startswith('-'):
            total_seconds *= -1
        
        return total_seconds
    
    @staticmethod
    def current_date():
        """Get current date as YYYY-MM-DD string using proper local time."""
        from gbebox.clock import clock
        local_datetime = clock.get_local_datetime_from_utc()
        year, month, day = local_datetime[:3]
        return f"{year}-{month:0>2}-{day:0>2}"
    
    @staticmethod
    def date_within_range(current_date, start_date, end_date=None):
        """
        Check if current date falls within the specified range.
        
        Args:
            current_date: Date to check (YYYY-MM-DD format)
            start_date: Range start date
            end_date: Range end date (None for open-ended range)
        """
        if end_date is None:
            return start_date <= current_date
        return start_date <= current_date <= end_date
    
    @staticmethod
    def compute_end_date(start_date, duration_days):
        """
        Compute end date given a start date and duration in days.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            duration_days: Number of days to add
            
        Returns:
            End date in YYYY-MM-DD format
        """
        year, month, day = map(int, start_date.split('-'))
        start_timestamp = time.mktime((year, month, day, 0, 0, 0, 0, 0))
        end_timestamp = start_timestamp + (duration_days * 24 * 60 * 60)
        
        end_year, end_month, end_day, _, _, _, _, _ = time.localtime(end_timestamp)
        return f"{end_year}-{end_month:0>2}-{end_day:0>2}"
    
    @staticmethod
    def time_within_range(start_time, end_time):
        """
        Check if current time falls within the specified time range.
        
        Uses proper local time calculation from UTC base.
        
        Args:
            start_time: Range start time (HH:MM:SS or HH:MM format)
            end_time: Range end time (HH:MM:SS or HH:MM format)
            
        Returns:
            bool: True if current time is within range
        """
        # Get current local time using proper timezone conversion
        from gbebox.clock import clock
        local_datetime = clock.get_local_datetime_from_utc()
        _, _, _, hours, minutes, seconds = local_datetime
        current_time = f"{hours:0>2}:{minutes:0>2}:{seconds:0>2}"
        
        def normalize_time(t):
            """Normalize time string to HH:MM:SS format."""
            parts = t.split(":")
            h = parts[0] if len(parts) > 0 else "00"
            m = parts[1] if len(parts) > 1 else "00"
            s = parts[2] if len(parts) > 2 else "00"
            return f"{h:0>2}:{m:0>2}:{s:0>2}"
        
        # Normalize input times
        start_time = normalize_time(start_time)
        end_time = normalize_time(end_time)
        
        # Handle overnight time range (e.g., 22:00 to 06:00)
        if start_time > end_time:
            return not (end_time < current_time < start_time)
        else:
            return start_time <= current_time <= end_time


class SystemUtils:
    """System-level utility functions for runtime detection and diagnostics."""
    
    @staticmethod
    def display_system_info():
        """Display system information including hardware ID, network info, and available sensors."""
        # Import at function level to avoid circular imports
        from gbebox.hardware import board
        from gbebox.networking import wlan  
        from gbebox.sensors import sensor
        
        print("Hardware ID:    " + board["id"])
        if board["mac"]:
            print("MAC address:    " + board["mac"])
            
        if wlan.ifconfig()[0]:     
            print("IP Address:     " + wlan.ifconfig()[0] + "\n")
        
        print("Available Sensors:")
        for sensor_info in sensor.get_available_sensors():
            print(sensor_info)
        print()


# Create global instances for backward compatibility
calc = TimeCalculator()
system = SystemUtils()