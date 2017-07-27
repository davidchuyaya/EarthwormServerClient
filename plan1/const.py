"""
Constants shared between the client and the server. This file should exist on both.
"""

PORT = 8888
MAX_DATA_SIZE = 1024

REQUEST_NAME = b"getName"
REQUEST_SIZE = b"getSize"
REQUEST_FILE = b"getFile"
REQUEST_END = b"end"
