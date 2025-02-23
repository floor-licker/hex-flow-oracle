import weakref
from typing import Dict, Any, Optional, Callable
from collections import Counter

class MemoryManager:
    """Advanced memory management with reference counting"""
    def __init__(self):
        self._objects: Dict[int, weakref.ref] = {}
        self._ref_counts = Counter()
        self._finalizers: Dict[int, Callable] = {}

    def register(self, obj: Any, finalizer: Optional[Callable] = None) -> int:
        obj_id = id(obj)
        self._objects[obj_id] = weakref.ref(obj, self._cleanup)
        self._ref_counts[obj_id] = 1
        if finalizer:
            self._finalizers[obj_id] = finalizer
        return obj_id

    def increment_ref(self, obj_id: int):
        self._ref_counts[obj_id] += 1

    def decrement_ref(self, obj_id: int):
        self._ref_counts[obj_id] -= 1
        if self._ref_counts[obj_id] <= 0:
            self._cleanup(self._objects[obj_id]) 