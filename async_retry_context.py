import asyncio
import threading

class AsyncRetryContext:
    """Advanced context manager using descriptor protocol for retry logic"""
    def __init__(self, max_retries=3, backoff_base=1.5, should_retry=lambda exc: True):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.should_retry = should_retry  # Lambda to determine retry eligibility
        self._local = threading.local()
        self._local.attempt = 0

    async def __aexit__(self, exc_type, exc, tb):
        if exc is not None and self._local.attempt < self.max_retries and self.should_retry(exc):
            self._local.attempt += 1
            delay = self.backoff_base ** self._local.attempt
            await asyncio.sleep(delay)
            return True
        return False

    # Example usage:
    # @AsyncRetryContext(should_retry=lambda exc: isinstance(exc, ConnectionError))
    # async def connect_to_service():
    #     ... 