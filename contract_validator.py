from typing import Any, Callable
import logging
from functools import wraps

class ContractValidatorMeta(type):
    """Metaclass for automatic contract validation"""
    def __new__(mcs, name, bases, namespace):
        for key, value in namespace.items():
            if getattr(value, '_is_contract_method', False):
                namespace[key] = mcs.validate_method(value)
        return super().__new__(mcs, name, bases, namespace)

    @staticmethod
    def validate_method(method):
        async def validated(*args, **kwargs):
            try:
                result = await method(*args, **kwargs)
                ContractValidatorMeta.validate_result(result)
                return result
            except Exception as e:
                logging.error(f"Contract call failed: {e}")
                raise
        return validated

def contract_method(validation_func: Callable[[Any], bool] = None):
    """Decorator for contract methods"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            if validation_func and not validation_func(result):
                raise ValueError(f"Contract validation failed for {func.__name__}")
            return result
        wrapper._is_contract_method = True
        return wrapper
    return decorator 