import asyncio
import websockets

class WebSocketPool:
    def __init__(self, url, pool_size=3):
        self.url = url
        self.pool_size = pool_size
        self.connections = []
        self.current = 0

    async def get_connection(self):
        MAX_RETRIES = 3
        BACKOFF_FACTOR = 1.5
        
        for attempt in range(MAX_RETRIES):
            try:
                if len(self.connections) < self.pool_size:
                    ws = await websockets.connect(self.url)
                    self.connections.append(ws)
                self.current = (self.current + 1) % len(self.connections)
                return self.connections[self.current]
            except Exception as e:
                delay = BACKOFF_FACTOR ** attempt
                print(f"Connection attempt {attempt + 1} failed. Retrying in {delay}s")
                await asyncio.sleep(delay)
        raise ConnectionError("Failed to establish WebSocket connection")

    async def close_all(self):
        await asyncio.gather(*[ws.close() for ws in self.connections]) 