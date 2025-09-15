"""
Network management for GBE Box.

Handles WiFi connection, monitoring, and network operations.
"""

import uasyncio as asyncio
import network
import time


class WiFiManager:
    """
    WiFi connection manager with improved error handling and monitoring.
    
    Converts the original static method approach to a proper instance-based API.
    """
    
    def __init__(self):
        self._wlan = network.WLAN(network.STA_IF)
    
    def connect(self, timeout=10, config=None):
        """
        Connect to WiFi network with enhanced validation.
        
        Args:
            timeout: Connection timeout in seconds
            config: WiFi configuration dict, or None to use stored config
            
        Returns:
            str: Status message describing connection result
        """
        if config is None:
            # Import here to avoid circular dependency
            from .storage import sd
            config = sd.wifi_file
        
        if not config:
            return "WiFi settings not found."
        
        network_name = config.get("NETWORK_NAME")
        if not network_name:
            return "WiFi Network Name is not set. Please configure WiFi."
        
        try:
            self._wlan.active(True)
            network_password = config.get("NETWORK_PASSWORD", "")
            self._wlan.connect(network_name, network_password)
            
            # Wait for connection with status monitoring
            while not self._wlan.isconnected() and timeout > 0:
                # Check for specific error conditions
                status = self._wlan.status()
                if status == network.STAT_WRONG_PASSWORD:
                    return f"WiFi connection failed: Wrong password for '{network_name}'"
                elif status == network.STAT_NO_AP_FOUND:
                    return f"WiFi connection failed: Network '{network_name}' not found"
                elif status == network.STAT_CONNECT_FAIL:
                    return f"WiFi connection failed: Unable to connect to '{network_name}'"
                
                time.sleep(1)
                timeout -= 1
            
            if self._wlan.isconnected():
                # Validate we have a proper IP address
                ip_config = self._wlan.ifconfig()
                if ip_config[0] == '0.0.0.0':
                    return f"Connected to '{network_name}' but no IP address assigned"
                return f"Connected to '{network_name}' ({ip_config[0]})"
            else:
                return f"Connection timeout: Unable to connect to '{network_name}' within {timeout} seconds"
        
        except KeyError as e:
            return f"Config key error: {e}"
        except Exception as e:
            return f"WiFi connection error: {e}"
    
    def disconnect(self):
        """Disconnect from WiFi network."""
        try:
            self._wlan.disconnect()
            self._wlan.active(False)
            return "Disconnected from WiFi"
        except Exception as e:
            return f"Error disconnecting: {e}"
    
    def is_connected(self):
        """Check if WiFi is connected."""
        return self._wlan.isconnected()
    
    
    
    async def check_connection(self, check_interval=900):
        """
        Continuously monitor WiFi connection and reconnect if needed.
        
        Enhanced for classroom reliability with smart retry logic.
        
        Args:
            check_interval: How often to check connection (seconds)
        """
        consecutive_failures = 0
        
        while True:
            await asyncio.sleep(check_interval)
            
            # Import here to avoid circular dependency
            from .storage import sd
            wifi_config = sd.wifi_file
            
            # Only check if WiFi is configured
            if wifi_config and wifi_config.get("NETWORK_NAME"):
                if not self._wlan.isconnected():
                    consecutive_failures += 1
                    print(f"WiFi disconnected (failure #{consecutive_failures}), attempting to reconnect...")
                    
                    # Smart retry with exponential backoff
                    max_attempts = min(3 + consecutive_failures, 6)  # 3-6 attempts based on failure history
                    base_timeout = 5
                    
                    success = False
                    for attempt in range(max_attempts):
                        timeout = base_timeout + (attempt * 2)  # Increasing timeout: 5, 7, 9, 11, 13, 15s
                        result = self.connect(timeout=timeout)
                        print(f"Reconnection attempt {attempt + 1}/{max_attempts}: {result}")
                        
                        if self._wlan.isconnected():
                            print("WiFi reconnection successful")
                            consecutive_failures = 0  # Reset failure count
                            success = True
                            break
                        
                        if attempt < max_attempts - 1:  # Don't wait after last attempt
                            await asyncio.sleep(2)  # Brief pause between attempts
                    
                    if not success:
                        print(f"WiFi reconnection failed after {max_attempts} attempts. Will retry in {check_interval} seconds.")
                else:
                    # Connection is good, reset failure counter
                    if consecutive_failures > 0:
                        consecutive_failures = 0
    
    @property
    def ifconfig(self):
        """Get network interface configuration."""
        return self._wlan.ifconfig() if self._wlan.isconnected() else None
    
    @property
    def ip_address(self):
        """Get current IP address."""
        config = self.ifconfig
        return config[0] if config else None


# Create global instances
wifi = WiFiManager()
wlan = wifi._wlan  # For backward compatibility