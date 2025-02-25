from asyncio import Queue, Event, CancelledError, sleep

class AsyncEventBuffer:
    """Buffered async iterator for event processing"""
    def __init__(self, max_size=1000):
        self.buffer = Queue(maxsize=max_size)
        self._done = Event()
        self._background_tasks = set()

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return await self.buffer.get()
        except CancelledError:
            if not self._done.is_set():
                raise
            raise StopAsyncIteration

    async def process_with_backpressure(self, event):
        if self.buffer.full():
            await self.apply_backpressure()
        await self.buffer.put(event)

    async def apply_backpressure(self):
        buffer_size = self.buffer.qsize()
        if buffer_size > self.buffer.maxsize * 0.9:
            delay = (buffer_size / self.buffer.maxsize) ** 2
            await sleep(delay) 