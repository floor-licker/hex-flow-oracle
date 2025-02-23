from typing import Any, TypeVar, Generic
from functools import partial

T = TypeVar('T')

class ContractMethodDescriptor(Generic[T]):
    """Advanced descriptor for contract method validation"""
    def __init__(self, validation_func=None, gas_limit=None):
        self.validation_func = validation_func
        self.gas_limit = gas_limit
        self._name = None

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, objtype=None) -> T:
        if obj is None:
            return self
        return partial(self.__call__, obj)

    async def __call__(self, instance, *args, **kwargs):
        result = await getattr(instance, f"_{self._name}")(*args, **kwargs)
        if self.validation_func and not await self.validation_func(result):
            raise ValueError(f"Validation failed for {self._name}")
        return result 