from typing import Dict, Type, TypeVar, Generic

T = TypeVar('T')

class DIContainer(Generic[T]):
    """Advanced dependency injection container"""
    def __init__(self):
        self._services: Dict[Type[T], T] = {}
        self._factories = {}
        self._singletons = set()

    def register(self, interface: Type[T], implementation: Type[T], singleton: bool = True):
        if singleton:
            self._singletons.add(interface)
        self._factories[interface] = implementation

    async def resolve(self, interface: Type[T]) -> T:
        if interface in self._services:
            return self._services[interface]

        impl = self._factories[interface]
        instance = await self._instantiate(impl)

        if interface in self._singletons:
            self._services[interface] = instance

        return instance 