import asyncio
from dataclasses import dataclass
from typing import Optional
import logging

@dataclass
class RetryConfig:
    base_delay: float = 1.0
    max_delay: float = 60.0
    max_retries: Optional[int] = None
    exponential_base: float = 2.0
    jitter: float = 0.1

class ExponentialBackoffStrategy:
    """Implements exponential backoff with jitter for retrying operations"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.attempt = 0
        self._reset_time = None

    async def wait(self) -> None:
        """Calculate and wait for the next retry interval"""
        self.attempt += 1
        
        if self.config.max_retries and self.attempt > self.config.max_retries:
            raise Exception("Max retry attempts exceeded")

        delay = min(
            self.config.base_delay * (self.config.exponential_base ** (self.attempt - 1)),
            self.config.max_delay
        )

        # Add jitter to prevent thundering herd
        jitter = delay * self.config.jitter
        actual_delay = delay + (asyncio.get_event_loop().time() % jitter)

        logging.debug(f"Retry attempt {self.attempt}, waiting {actual_delay:.2f}s")
        await asyncio.sleep(actual_delay)

    async def handle_error(self, error: Exception) -> None:
        """Handle specific error types differently"""
        if isinstance(error, (ConnectionError, TimeoutError)):
            # Network errors get exponential backoff
            await self.wait()
        else:
            # Other errors might need different handling
            logging.error(f"Unhandled error in retry strategy: {error}")
            raise error

    def reset(self) -> None:
        """Reset the retry counter"""
        self.attempt = 0
        self._reset_time = None 