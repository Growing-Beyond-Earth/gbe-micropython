"""
JPretty MicroPython Library

This library provides a function for formatting JSON data into a human-readable string format with customizable 
indentation. It recursively formats dictionaries, lists, and other JSON-compatible objects to improve readability. 
This tool is part of the Growing Beyond Earth® project and is designed to assist with organizing and presenting 
JSON configuration and data files used in the GBE control circuit hardware.

Growing Beyond Earth® and this software are developed by Fairchild Tropical Botanic Garden, Miami, Florida, USA.

Date: September 14, 2024

For more information, visit: https://www.fairchildgarden.org/gbe
"""

import json

def jpretty(data, indent=4):
    def recursive_format(obj, level=0):
        result = ""
        indent_str = ' ' * indent * level
        if isinstance(obj, dict):
            result += "{\n"
            for i, (key, value) in enumerate(obj.items()):
                if i > 0:
                    result += ",\n"
                result += indent_str + ' ' * indent + '"' + str(key) + '": ' + recursive_format(value, level + 1)
            result += "\n" + indent_str + "}"
        elif isinstance(obj, list):
            result += "[\n"
            for i, item in enumerate(obj):
                if i > 0:
                    result += ",\n"
                result += indent_str + ' ' * indent + recursive_format(item, level + 1)
            result += "\n" + indent_str + "]"
        elif isinstance(obj, str):
            result += '"' + obj + '"'
        elif isinstance(obj, bool):
            result += "true" if obj else "false"
        elif obj is None:
            result += "null"
        elif isinstance(obj, (int, float)):
            result += str(obj)
        else:
            # For other types, convert to string and quote it
            result += '"' + str(obj) + '"'
        return result
    
    json_string = recursive_format(data)
    return(json_string)
