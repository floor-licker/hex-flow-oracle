import asyncio
import time
from collections import deque
from enum import Enum
from dataclasses import dataclass

class CircuitState(Enum):
    CLOSED = " 