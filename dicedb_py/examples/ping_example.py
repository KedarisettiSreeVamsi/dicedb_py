"""
Example showing how to use the DiceDB Python client to ping the server.
"""
import sys
import time
from dicedb_py import Client

def main():
    # Create a DiceDB client
    try:
        client = Client("localhost", 7379)
        print(f"Connected to DiceDB server with client ID: {client.id}")
        
        # Send a PING command
        response = client.fire_string("PING")
        
        if response.err:
            print(f"Error: {response.err}")
            return 1
        
        print(f"Server response: {response.v_str}")
        
        # Close the connection
        client.close()
        return 0
        
    except ConnectionError as e:
        print(f"Connection error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())