import asyncio
import threading
import weakref
from typing import TypeVar, Generic, Callable, Any
from asyncio import Lock
from functools import wraps

T = TypeVar('T')

class AsyncRetryContext:
    """Advanced context manager using descriptor protocol for retry logic"""
    def __init__(self, max_retries=3, backoff_base=1.5, should_retry=lambda exc: True):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.should_retry = should_retry
        self._local = threading.local()
        self._local.attempt = 0

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self:
                return await func(*args, **kwargs)
        return wrapper

    async def __aenter__(self):
        self._local.attempt = 0
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc is not None and self._local.attempt < self.max_retries and self.should_retry(exc): 