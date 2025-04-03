"""
I/O operations for DiceDB client-server communication.
"""
import socket
import struct
import pickle
from typing import Tuple

from .wire import Command, Response, ValueType


# Constants
MAX_REQUEST_SIZE = 32 * 1024 * 1024  # 32 MB
IO_BUFFER_SIZE = 16 * 1024  # 16 KB
IDLE_TIMEOUT = 30 * 60  # 30 minutes


def serialize(cmd: Command) -> bytes:
    """Serialize a Command object to bytes."""
    return pickle.dumps(cmd)


def deserialize(data: bytes) -> Response:
    """Deserialize bytes to a Response object."""
    try:
        return pickle.loads(data)
    except Exception as e:
        return Response(err=f"Failed to deserialize response: {str(e)}")


def read(conn: socket.socket) -> Response:
    """Read a Response from a socket connection."""
    result = bytearray()
    
    while True:
        try:
            chunk = conn.recv(IO_BUFFER_SIZE)
            if not chunk:
                break
                
            if len(result) + len(chunk) > MAX_REQUEST_SIZE:
                return Response(err="Request too large")
                
            result.extend(chunk)
            
            if len(chunk) < IO_BUFFER_SIZE:
                break
                
        except socket.error as e:
            return Response(err=str(e))
    
    if not result:
        return Response(err="Empty response or connection closed")
    
    return deserialize(bytes(result))


def write(conn: socket.socket, cmd: Command) -> bool:
    """Write a Command to a socket connection."""
    try:
        data = serialize(cmd)
        conn.sendall(data)
        return True
    except Exception as e:
        return False