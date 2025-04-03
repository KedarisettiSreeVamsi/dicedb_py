"""
DiceDB client for Python.
"""
import socket
import threading
import uuid
import time
import io
from typing import List, Dict, Callable, Optional, Tuple, Any, Union

from . import io as dice_io
from .wire import Command, Response, ValueType


class ClientOption:
    """Class to hold client configuration options."""
    def __init__(self, option_func):
        self.option_func = option_func

    def apply(self, client):
        """Apply the option to the client."""
        self.option_func(client)


def WithID(client_id: str) -> ClientOption:
    """Set a custom ID for the client."""
    def option_func(client):
        client.id = client_id
    return ClientOption(option_func)


class Client:
    """DiceDB client."""
    
    def __init__(self, host: str, port: int, *options: ClientOption):
        """
        Initialize a new DiceDB client.
        
        Args:
            host: The hostname or IP address of the DiceDB server
            port: The port number of the DiceDB server
            options: Optional client configuration options
        """
        self.host = host
        self.port = port
        self.id = str(uuid.uuid4())
        self.conn = None
        self.watch_conn = None
        self.watch_ch = None
        self._lock = threading.RLock()
        self._watch_thread = None
        
        # Apply options
        for option in options:
            option.apply(self)
        
        # Connect to the server
        self._connect()
        
        # Perform handshake
        resp = self.fire(Command(cmd="HANDSHAKE", args=[self.id, "command"]))
        if resp.err:
            raise ConnectionError(f"Could not complete the handshake: {resp.err}")
    
    def _connect(self) -> None:
        """Establish a connection to the DiceDB server."""
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.settimeout(5)  # 5 second timeout
            self.conn.connect((self.host, self.port))
        except socket.error as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {str(e)}")
    
    def _fire(self, cmd: Command, conn: socket.socket) -> Response:
        """Send a command to the server and return the response."""
        if not dice_io.write(conn, cmd):
            return Response(err="Failed to write command to socket")
        
        return dice_io.read(conn)
    
    def fire(self, cmd: Command) -> Response:
        """Send a command to the server and return the response."""
        with self._lock:
            result = self._fire(cmd, self.conn)
            if result.err:
                if self.check_and_reconnect(result.err):
                    return self.fire(cmd)
            return result
    
    def fire_string(self, cmd_str: str) -> Response:
        """Send a command string to the server and return the response."""
        cmd_str = cmd_str.strip()
        tokens = cmd_str.split()
        
        cmd = tokens[0]
        args = tokens[1:] if len(tokens) > 1 else []
        
        return self.fire(Command(cmd=cmd, args=args))
    
    def check_and_reconnect(self, error: str) -> bool:
        """Check if the error is due to a broken connection and try to reconnect."""
        if "EOF" in error or "Broken pipe" in error:
            print(f"Error in connection: {error}. Reconnecting...")
            
            try:
                with self._lock:
                    if self.conn:
                        self.conn.close()
                    
                    self._connect()
                    
                    # Re-authenticate
                    resp = self._fire(Command(cmd="HANDSHAKE", args=[self.id, "command"]), self.conn)
                    if resp.err:
                        print(f"Failed to reconnect: {resp.err}")
                        return False
                    
                    return True
            except Exception as e:
                print(f"Failed to reconnect: {str(e)}")
                return False
        
        return False
    
    def watch_ch(self) -> Tuple[Optional[threading.Event], Response]:
        """
        Create a channel to watch for server events.
        
        Returns:
            A tuple containing a threading.Event to stop watching and a Response channel
        """
        with self._lock:
            if self.watch_ch is not None:
                return self.watch_ch
            
            self.watch_ch = threading.Event()
            self.watch_queue = []
            self.watch_condition = threading.Condition()
            
            try:
                self.watch_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.watch_conn.settimeout(5)
                self.watch_conn.connect((self.host, self.port))
                
                # Handshake for watch connection
                resp = self._fire(Command(cmd="HANDSHAKE", args=[self.id, "watch"]), self.watch_conn)
                if resp.err:
                    raise ConnectionError(f"Could not complete the watch handshake: {resp.err}")
                
                # Start watch thread
                self._watch_thread = threading.Thread(target=self._watch, daemon=True)
                self._watch_thread.start()
                
                return self.watch_ch, self.watch_queue
            
            except Exception as e:
                self.watch_ch = None
                raise ConnectionError(f"Failed to setup watch connection: {str(e)}")
    
    def _watch(self) -> None:
        """Background thread that watches for server events."""
        while not self.watch_ch.is_set():
            try:
                resp = dice_io.read(self.watch_conn)
                
                with self.watch_condition:
                    self.watch_queue.append(resp)
                    self.watch_condition.notify_all()
                
            except Exception as e:
                if not self.check_and_reconnect(str(e)):
                    with self.watch_condition:
                        error_resp = Response(err=f"Watch error: {str(e)}")
                        self.watch_queue.append(error_resp)
                        self.watch_condition.notify_all()
                    
                    # Break out of the loop if we can't reconnect
                    break
    
    def close(self) -> None:
        """Close the client connection."""
        with self._lock:
            if self.watch_ch:
                self.watch_ch.set()
            
            if self.conn:
                self.conn.close()
            
            if self.watch_conn:
                self.watch_conn.close()


def get_or_create_client(client: Optional[Client] = None, host: str = "localhost", port: int = 7379) -> Client:
    """
    Get an existing client or create a new one.
    
    Args:
        client: An existing client to reuse, or None to create a new one
        host: The hostname or IP address of the DiceDB server (if creating a new client)
        port: The port number of the DiceDB server (if creating a new client)
    
    Returns:
        A DiceDB client
    """
    if client is None:
        return Client(host, port)
    
    # If the client is provided but not connected, create a new one with the same settings
    try:
        new_client = Client(client.host, client.port)
        
        if client.conn:
            client.conn.close()
        
        return new_client
    except Exception as e:
        raise ConnectionError(f"Failed to create new client: {str(e)}")