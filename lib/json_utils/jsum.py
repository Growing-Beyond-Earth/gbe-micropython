"""
JSum MicroPython Library

This library is an adaptation of the JSum project developed by Fraunhofer FOKUS, which provides a method to calculate 
checksums of JSON objects. It has been modified for MicroPython to generate checksums of JSON data using different 
hashing algorithms (SHA-1 and SHA-256) with customizable encoding (hex or base64). This library is designed to assist 
with client-server data comparison in the Growing Beyond Earth® (GBE) control circuit project.

Original source: https://github.com/fraunhoferfokus/JSum
Licensed under the GNU Affero General Public License v3.0: https://www.gnu.org/licenses/

This adapted version is distributed under the same terms of the GNU Affero General Public License v3.0.

Growing Beyond Earth® and this software are developed by Fairchild Tropical Botanic Garden, Miami, Florida, USA.

Date: September 14, 2024

For more information, visit: https://www.fairchildgarden.org/gbe
"""

import ujson
import hashlib
import ubinascii

def _serialize(obj):
    if isinstance(obj, list):
        # Serialize a list (array)
        return '[{}]'.format(','.join([_serialize(el) for el in obj]))
    elif isinstance(obj, dict):
        # Serialize a dictionary (object)
        acc = '{'
        keys = sorted(obj.keys())  # Sort the keys for consistent ordering
        acc += '{}'.format(ujson.dumps(keys).replace(' ', ''))  # Serialize sorted keys without spaces
        for key in keys:
            acc += _serialize(obj[key]) + ','
        acc = acc.rstrip(',')  # Remove trailing comma
        acc += '}'  # Close object correctly
        return acc
    else:
        # Serialize a primitive value (string, int, etc.)
        return '{}'.format(ujson.dumps(obj).replace(' ', ''))

def serialize(obj):
    return _serialize(obj)

def digest(obj, hash_algorithm='sha1', encoding='base64'):
    # Select the appropriate hash algorithm
    if hash_algorithm == 'sha256':
        hash_func = hashlib.sha256()
    elif hash_algorithm == 'sha1':
        hash_func = hashlib.sha1()
    else:
        raise ValueError("Unsupported hash algorithm")

    serialized_obj = serialize(obj)
    # Update the hash object with the serialized data
    hash_func.update(serialized_obj.encode('utf-8'))

    # Return the digest in the requested encoding
    if encoding == 'hex':
        return ubinascii.hexlify(hash_func.digest()).decode('utf-8')
    elif encoding == 'base64':
        return ubinascii.b2a_base64(hash_func.digest()).decode().strip()
    else:
        return hash_func.digest()


