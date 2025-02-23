from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum
import time
import asyncio
from collections import deque
from rate_monitor import RateMonitor

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Stop all requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitStats:
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0

class AdaptiveRateLimiter:
    def __init__(
        self,
        initial_rate: int = 10,
        window_size: float = 1.5,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        adaptive_factor: float = 0.5
    ):
        self.current_rate = initial_rate
        self.window_size = window_size
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.adaptive_factor = adaptive_factor
        
        self.request_times = deque()
        self.circuit_state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._lock = asyncio.Lock()
        self.monitor = RateMonitor(window_size=window_size)
        asyncio.create_task(self.monitor.monitor_loop())

    async def acquire(self) -> bool:
        async with self._lock:
            now = time.time()
            
            # Clean old requests
            while self.request_times and self.request_times[0] < now - self.window_size:
                self.request_times.popleft()

            # Check circuit breaker
            if self.circuit_state == CircuitState.OPEN:
                if now - self.stats.last_failure_time > self.recovery_timeout:
                    self.circuit_state = CircuitState.HALF_OPEN
                else:
                    return False

            # Check rate limit
            if len(self.request_times) >= self.current_rate:
                self._handle_failure()
                return False

            # Allow request
            self.request_times.append(now)
            allowed = True

            # If request allowed, update monitor
            if allowed:
                self.monitor.add_request()
            return allowed

    def _handle_failure(self):
        self.stats.failure_count += 1
        self.stats.last_failure_time = time.time()
        
        if self.stats.failure_count >= self.failure_threshold:
            self.circuit_state = CircuitState.OPEN
            self.current_rate = max(1, int(self.current_rate * self.adaptive_factor))

    def _handle_success(self):
        self.stats.success_count += 1
        self.stats.last_success_time = time.time()
        
        if self.circuit_state == CircuitState.HALF_OPEN:
            self.circuit_state = CircuitState.CLOSED
            self.current_rate = min(15, int(self.current_rate / self.adaptive_factor))

    def close(self):
        self.monitor.close() 