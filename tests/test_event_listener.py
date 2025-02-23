import pytest
import asyncio
from unittest.mock import Mock, patch
from event_listener import AsyncEventBuffer, RateLimiter

@pytest.mark.asyncio
async def test_event_buffer_backpressure():
    buffer = AsyncEventBuffer(max_size=5)
    
    # Test backpressure activation
    for i in range(6):
        await buffer.process_with_backpressure({"event": f"test_{i}"})
    
    assert buffer.buffer.qsize() == 5

@pytest.mark.asyncio
async def test_rate_limiter():
    limiter = RateLimiter(rate_limit=2, time_window=1.0)
    
    # Should not delay
    assert await limiter.acquire()
    assert await limiter.acquire()
    
    # Should delay
    start_time = asyncio.get_event_loop().time()
    assert await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start_time
    assert elapsed >= 0.5 