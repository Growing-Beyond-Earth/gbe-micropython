"""
SD card storage management for GBE Box.

Handles SD card mounting, file operations, and configuration management.
"""

import uos
import json
from drivers import sdcard
from machine import Pin
from .hardware import board, spi0


class SDCardManager:
    """
    SD card storage manager with improved error handling.
    
    Addresses the original static method inconsistencies by providing
    a clear instance-based API for storage operations.
    """
    
    def __init__(self):
        self._detect_pin = Pin(board["pins"]["sdcard_cd"], Pin.IN, Pin.PULL_UP)
        
        # Cached configuration files
        self._wifi_config = None
        self._timezone_config = None
        self._program_config = None
        
        # Callback for program configuration changes
        self._program_change_callback = None
        
        # State tracking for SD card removal/insertion recovery
        self._last_known_state = self.is_present()
        self._mount_state = False
        self._initial_boot = True  # Flag to distinguish initial boot from reinsertion
        
        # Load settings on initialization
        self.load_settings()
    
    def mount(self):
        """Mount the SD card if present and readable with recovery logic."""
        current_state = self.is_present()
        
        # Detect SD card removal and insertion
        if self._last_known_state != current_state:
            if current_state:
                print("SD card inserted, attempting to mount...")
            else:
                print("SD card removed")
                self._mount_state = False
                # Force unmount when card is removed
                try:
                    uos.umount('/sd')
                except:
                    pass
            self._last_known_state = current_state
        
        # No card present
        if not current_state:
            self._mount_state = False
            return False
        
        # Card is present - check if already properly mounted
        try:
            if 'sd' in uos.listdir('/') and self._mount_state:
                # Verify mount is actually working with a quick test
                uos.listdir('/sd')
                return True
        except (OSError, Exception):
            # Mount exists but not working, need to remount
            print("SD card mount corrupted, attempting recovery...")
            self._mount_state = False
            try:
                uos.umount('/sd')
            except:
                pass  # Ignore unmount errors
        
        # Card is present but not mounted or needs remounting
        # Check if this appears to be a fresh insertion - state already updated above
        was_just_inserted = (current_state and not self._mount_state)
        
        # For fresh insertions OR failed mount state, reset SPI to clear any residual state
        if was_just_inserted or not self._mount_state:
            try:
                # Reinitialize SPI to clear any stale state from previous card
                spi0.deinit()
                import time
                time.sleep(0.2)
                # Initialize SPI with just baudrate - pins are fixed in hardware setup
                spi0.init(baudrate=40000000)
                time.sleep(0.1)  # Brief pause after SPI init
            except Exception as e:
                print(f"SPI reset warning: {e}")
        
        for attempt in range(3):  # Try up to 3 times
            try:
                if attempt > 0:
                    # print(f"Mounting SD card (attempt {attempt + 1}/3)...")
                    import time
                    time.sleep(0.5)  # Wait between attempts
                else:
                    pass
                    # print("Mounting SD card...")
                
                # Give freshly inserted cards extra time to stabilize
                if was_just_inserted and attempt == 0:
                    import time
                    time.sleep(1.5)  # Longer delay for fresh insertions
                elif attempt > 0:
                    import time 
                    time.sleep(0.2 * attempt)  # Progressive delay
                
                card = sdcard.SDCard(spi0, Pin(board["pins"]["spi0_cs_sdcard"]))
                vfs = uos.VfsFat(card)
                uos.mount(vfs, '/sd')
                self._mount_state = True
                print("SD card mounted successfully")
                
                # Load/reload settings when card is mounted
                if was_just_inserted:
                    # print("Loading settings from SD card...")
                    self.load_settings()
                
                # Clear initial boot flag after first successful mount
                self._initial_boot = False
                    
                return True
                
            except OSError as e:
                if e.errno == 1:  # EPERM
                    print(f"SD card permission error (attempt {attempt + 1}/3): Card may need more time to stabilize")
                    if attempt == 2:  # Last attempt
                        print("SD card mount failed after 3 attempts - card may be corrupted or incompatible")
                else:
                    print(f"SD card OS error (attempt {attempt + 1}/3): {e}")
                
                if attempt < 2:  # Not the last attempt
                    continue
                    
            except Exception as e:
                print(f"SD card error (attempt {attempt + 1}/3): {e}")
                if attempt < 2:  # Not the last attempt
                    continue
        
        # All attempts failed
        self._mount_state = False
        print("SD card mount failed - will retry on next access")
        
        # Brief visual error indication for final failure
        try:
            from .indicator import indicator
            indicator.on("red")
            import time
            time.sleep(0.5)
            indicator.off()
        except:
            pass  # Don't let indicator errors break SD operations
            
        return False
    
    def unmount(self):
        """Safely unmount the SD card."""
        try:
            uos.umount('/sd')
            self._mount_state = False
            return True
        except Exception as e:
            print(f"Error unmounting SD card: {e}")
            return False
    
    def is_mounted(self):
        """Check if SD card is currently mounted and working."""
        try:
            if 'sd' in uos.listdir('/'):
                # Verify the mount is actually functional
                uos.listdir('/sd')
                return True
        except (OSError, Exception):
            # Mount exists but isn't working properly
            self._mount_state = False
        return False
    
    def is_present(self):
        """Check if SD card is physically present."""
        return self._detect_pin.value() == 0
    
    def _copy_default_to_sd(self, filename):
        """Copy a default file to the SD card with pretty formatting."""
        try:
            with open(f'/defaults/{filename}', 'r') as src:
                data = json.load(src)
                
                # Try to use jpretty if available
                try:
                    from json_utils import jpretty
                    formatted_data = jpretty.jpretty(data)
                except ImportError:
                    formatted_data = json.dumps(data, indent=2)
                
                with open(f'/sd/{filename}', 'w') as dst:
                    dst.write(formatted_data)
        except Exception as e:
            print(f"Error copying {filename} to SD card: {e}")
    
    def _validate_json(self, filepath):
        """Validate that a file contains valid JSON."""
        try:
            with open(filepath, 'r') as f:
                json.load(f)
            return True
        except Exception as e:
            print(f"Invalid JSON file {filepath}: {e}")
            return False
    
    def _load_json(self, filepath):
        """Load and return JSON data from a file."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON file {filepath}: {e}")
            return None
    
    def load_settings(self):
        """Load configuration settings from SD card or defaults."""
        if self.mount():
            if self.is_mounted():
                # Handle WiFi settings
                if ('wifi_settings.json' not in uos.listdir('/sd') or 
                    not self._validate_json('/sd/wifi_settings.json')):
                    self._copy_default_to_sd('wifi_settings.json')
                self._wifi_config = self._load_json('/sd/wifi_settings.json')
                
                # Handle timezone settings
                if ('timezone.json' not in uos.listdir('/sd') or 
                    not self._validate_json('/sd/timezone.json')):
                    self._copy_default_to_sd('timezone.json')
                self._timezone_config = self._load_json('/sd/timezone.json')
                
                # Handle program settings
                if ('program.json' not in uos.listdir('/sd') or 
                    not self._validate_json('/sd/program.json')):
                    self._copy_default_to_sd('program.json')
                old_config = self._program_config
                self._program_config = self._load_json('/sd/program.json')
                
                # Notify if program configuration changed
                if old_config != self._program_config:
                    self._notify_program_changed()
            else:
                print("SD card mounted but no files found.")
                self._wifi_config = None
                self._timezone_config = None
                self._program_config = None
        else:
            # Load from defaults if SD card not available
            print("SD card not mounted, loading from /defaults")
            self._wifi_config = self._load_json('/defaults/wifi_settings.json')
            self._timezone_config = self._load_json('/defaults/timezone.json')
            old_config = self._program_config
            self._program_config = self._load_json('/defaults/program.json')
            
            # Notify if program configuration changed
            if old_config != self._program_config:
                self._notify_program_changed()
        
        return self._wifi_config, self._timezone_config, self._program_config
    
    @property
    def wifi_file(self):
        """Get WiFi configuration."""
        return self._wifi_config
    
    @property
    def tz_file(self):
        """Get timezone configuration."""
        return self._timezone_config
    
    @property
    def program_json(self):
        """Get program configuration."""
        return self._program_config
    
    def register_program_change_callback(self, callback):
        """Register a callback to be called when program configuration changes."""
        self._program_change_callback = callback
    
    def _notify_program_changed(self):
        """Notify registered callback that program configuration has changed."""
        if self._program_change_callback:
            try:
                self._program_change_callback()
            except Exception as e:
                print(f"Error in program change callback: {e}")
    
    def save_program(self, program_data):
        """Save program configuration to SD card with recovery."""
        if self.mount():
            try:
                # Try to use jpretty formatting if available
                try:
                    from json_utils import jpretty
                    formatted_data = jpretty.jpretty(program_data)
                except ImportError:
                    formatted_data = json.dumps(program_data, indent=2)
                
                with open('/sd/program.json', 'w') as f:
                    f.write(formatted_data)
                old_config = self._program_config
                self._program_config = program_data
                print("Program configuration saved to SD card")
                
                # Notify if program configuration changed
                if old_config != self._program_config:
                    self._notify_program_changed()
                    
                return True
            except OSError as e:
                print(f"SD card I/O error saving program: {e}")
                print("SD card may have been removed during save operation")
                return False
            except Exception as e:
                print(f"Error saving program to SD card: {e}")
                return False
        else:
            print("Cannot save program - SD card not available")
            return False
    
    def read_file(self, filepath):
        """Read a file from the SD card."""
        if self.mount():
            try:
                with open(f'/sd/{filepath}', 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading file {filepath}: {e}")
        return None
    
    def write_file(self, filepath, content):
        """Write content to a file on the SD card."""
        if self.mount():
            try:
                with open(f'/sd/{filepath}', 'w') as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"Error writing file {filepath}: {e}")
        return False
    
    def list_files(self, path='/sd'):
        """List files in the specified SD card directory."""
        if self.mount():
            try:
                return uos.listdir(path)
            except Exception as e:
                print(f"Error listing files in {path}: {e}")
        return []


# Create global instance
sd = SDCardManager()