"""
Application Logic and Utilities for GBE Box

This package contains the application-level logic and utilities for the 
Growing Beyond Earth control system, separate from the hardware abstraction layer.

Modules:
- logic: Program execution engine, data logging, watchdog, and garbage collection
- utils: Time calculations and utility functions
"""

# Import application logic classes
from .logic import ProgramEngine, WatchdogManager, DataLogger, GarbageCollector, Run

# Import utility classes
from .utils import TimeCalculator, calc

# Export all classes for easy access
__all__ = [
    # Application logic
    'ProgramEngine', 'WatchdogManager', 'DataLogger', 'GarbageCollector', 'Run',
    
    # Utilities
    'TimeCalculator', 'calc'
]