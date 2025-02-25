from typing import Generic
import weakref
from threading import Lock

class WeakCache(Generic[T]):
    """Advanced caching system using weak references"""
    def __init__(self):
        self._cache = weakref.WeakValueDictionary()
        self._pending = weakref.WeakSet()
        self._lock = Lock()

    async def get_or_create(self, key: str, factory: callable) -> T:
        """Get item from cache or create using factory lambda"""
        async with self._lock:
            if key in self._cache:
                return self._cache[key]
            
            result = await factory()  # Factory is now a lambda
            self._cache[key] = result
            self._pending.add(result)
            return result

    # Example usage:
    # token_info = await cache.get_or_create(
    #     f"token_{address}",
    #     lambda: fetch_token_info(address)
    # ) 