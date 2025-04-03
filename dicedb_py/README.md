# dicedb-py

Python client for [DiceDB](https://github.com/dicedb/dice).

## Installation

```bash
pip install dicedb-py
```

Or install directly from the source:

```bash
pip install git+https://github.com/dicedb/dicedb-py.git@v1.0.4
```

## Getting Started

To start using DiceDB with Python, you can use the following example:

```python
from dicedb_py import Client

# Create a new client
client = Client("localhost", 7379)

# Send a command
response = client.fire_string("PING")
print(f"Server response: {response.v_str}")  # Should print "PONG"

# Clean up
client.close()
```

For more examples, check out the [examples](https://github.com/dicedb/dicedb-py/tree/master/examples) directory.

## License

BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.