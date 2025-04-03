"""
Protocol buffer message types for DiceDB client-server communication.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Any
from enum import Enum


@dataclass
class Command:
    """Command message sent to the DiceDB server."""
    cmd: str
    args: List[str] = None

    def __post_init__(self):
        if self.args is None:
            self.args = []


class ValueType(Enum):
    """Enum for response value types."""
    NIL = 'nil'
    INT = 'int'
    STR = 'str'
    FLOAT = 'float'
    BYTES = 'bytes'


@dataclass
class Response:
    """Response message received from the DiceDB server."""
    err: str = ""
    value_type: ValueType = None
    value: Any = None
    attrs: Dict[str, Any] = None
    v_list: List[Any] = None
    v_ss_map: Dict[str, str] = None

    @property
    def v_nil(self) -> bool:
        """Get nil value."""
        return self.value_type == ValueType.NIL

    @property
    def v_int(self) -> int:
        """Get integer value."""
        return self.value if self.value_type == ValueType.INT else 0

    @property
    def v_str(self) -> str:
        """Get string value."""
        return self.value if self.value_type == ValueType.STR else ""

    @property
    def v_float(self) -> float:
        """Get float value."""
        return self.value if self.value_type == ValueType.FLOAT else 0.0

    @property
    def v_bytes(self) -> bytes:
        """Get bytes value."""
        return self.value if self.value_type == ValueType.BYTES else b""