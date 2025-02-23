import asyncio
from asyncio import (
    Queue, Event, Lock, gather, sleep,
    CancelledError, TimeoutError
)
import json
import websockets
import logging
from datetime import datetime
import weakref
from typing import TypeVar, Generic
from functools import wraps
import threading

from config import (
    quicknode_ws_url, 
    uniswap_v2_factory_address,
    uniswap_v3_factory_address,
    v2_pair_created_topic,
    v3_pool_created_topic,
    CLEAN_MODE
)
from token_security import check_token_security

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('events.log'),
        logging.StreamHandler()
    ]
)

T = TypeVar('T')

class AsyncRetryContext:
    """Advanced context manager using descriptor protocol for retry logic"""
    def __init__(self, max_retries=3, backoff_base=1.5):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._local = threading.local()  # Use threading.local() instead of asyncio.Local
        self._local.attempt = 0  # Initialize attempt counter

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
        if exc is not None and self._local.attempt < self.max_retries:
            self._local.attempt += 1
            delay = self.backoff_base ** self._local.attempt
            await asyncio.sleep(delay)
            return True
        return False

class WeakCache(Generic[T]):
    """Advanced caching system using weak references"""
    def __init__(self):
        self._cache = weakref.WeakValueDictionary()
        self._pending = weakref.WeakSet()
        self._lock = Lock()

    async def get_or_create(self, key: str, factory: callable) -> T:
        async with self._lock:
            if key in self._cache:
                return self._cache[key]
            
            result = await factory()
            self._cache[key] = result
            self._pending.add(result)
            return result

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

async def handle_v2_event(log):
    """Handle V2 PairCreated event"""
    token0 = "0x" + log["topics"][1][26:]
    token1 = "0x" + log["topics"][2][26:]
    pair_address = "0x" + log["data"][26:66]
    
    token0_trusted = check_token_security(token0)
    token1_trusted = check_token_security(token1)
    
    if CLEAN_MODE:
        if token0_trusted and token1_trusted:
            print(f"Trusted V2 Pair: Token0: {token0}, Token1: {token1}, Pair: {pair_address}")
    else:
        print("\nV2 PairCreated event:")
        print(f"Token0: {token0}")
        print(f"Token1: {token1}")
        print(f"Pair Address: {pair_address}")
        print(json.dumps(log, indent=4))

async def handle_v3_event(log):
    """Handle V3 PoolCreated event"""
    token0 = "0x" + log["topics"][1][26:]
    token1 = "0x" + log["topics"][2][26:]
    fee_tier = int(log["topics"][3], 16)  # V3 specific
    pool_address = "0x" + log["data"][26:66]
    
    token0_trusted = check_token_security(token0)
    token1_trusted = check_token_security(token1)
    
    if CLEAN_MODE:
        if token0_trusted and token1_trusted:
            print(f"Trusted V3 Pool: Token0: {token0}, Token1: {token1}, Fee: {fee_tier}, Pool: {pool_address}")
    else:
        print("\nV3 PoolCreated event:")
        print(f"Token0: {token0}")
        print(f"Token1: {token1}")
        print(f"Fee Tier: {fee_tier}")
        print(f"Pool Address: {pool_address}")
        print(json.dumps(log, indent=4))

class RateLimiter:
    def __init__(self, rate_limit=10, time_window=1.0):
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.tokens = rate_limit
        self.last_update = asyncio.get_event_loop().time()

    async def acquire(self):
        now = asyncio.get_event_loop().time()
        time_passed = now - self.last_update
        self.tokens = min(self.rate_limit, self.tokens + time_passed * (self.rate_limit / self.time_window))
        self.last_update = now

        if self.tokens < 1:
            wait_time = (1 - self.tokens) * (self.time_window / self.rate_limit)
            await asyncio.sleep(wait_time)
            return await self.acquire()

        self.tokens -= 1
        return True

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

class EventProcessor:
    def __init__(self):
        self.queue = Queue()
        self.batch_size = 10
        self.batch_timeout = 1.0
        self.address_lookup = AddressLookup()

    async def process_batch(self, batch):
        try:
            tasks = []
            for event in batch:
                if event.get("params") and event.get("params").get("result"):
                    tasks.append(self.address_lookup.route_event(event["params"]["result"]))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions from the batch
            for result in results:
                if isinstance(result, Exception):
                    logging.error(f"Error processing event: {result}")
                    
        except Exception as e:
            logging.error(f"Batch processing error: {e}")

    async def process_events(self):
        while True:
            batch = []
            try:
                # Get first event or wait for timeout
                batch.append(await asyncio.wait_for(
                    self.queue.get(), 
                    timeout=self.batch_timeout
                ))
                
                # Get additional events if available
                while len(batch) < self.batch_size:
                    try:
                        batch.append(self.queue.get_nowait())
                    except asyncio.QueueEmpty:
                        break
                
                # Process batch
                await self.process_batch(batch)
                
            except asyncio.TimeoutError:
                if batch:
                    await self.process_batch(batch)

class AddressLookup:
    def __init__(self):
        self.v2_address = uniswap_v2_factory_address.lower()
        self.v3_address = uniswap_v3_factory_address.lower()
        self.address_map = {
            self.v2_address: handle_v2_event,
            self.v3_address: handle_v3_event
        }

    async def route_event(self, log):
        handler = self.address_map.get(log["address"].lower())
        if handler:
            await handler(log)

@AsyncRetryContext()
async def listen_for_pair_created_events():
    event_buffer = AsyncEventBuffer()
    weak_cache = WeakCache()
    rate_limiter = RateLimiter(rate_limit=10, time_window=1.0)
    
    while True:
        try:
            async with websockets.connect(quicknode_ws_url) as ws:
                # Subscribe to events with rate limiting
                subscriptions = [
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "eth_subscribe",
                        "params": [
                            "logs",
                            {
                                "address": uniswap_v2_factory_address,
                                "topics": [v2_pair_created_topic]
                            }
                        ]
                    },
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "eth_subscribe",
                        "params": [
                            "logs",
                            {
                                "address": uniswap_v3_factory_address,
                                "topics": [v3_pool_created_topic]
                            }
                        ]
                    }
                ]

                # Subscribe with rate limiting
                for sub in subscriptions:
                    await rate_limiter.acquire()
                    await ws.send(json.dumps(sub))
                    response = await ws.recv()
                    
                    # Check for subscription errors
                    resp_data = json.loads(response)
                    if "error" in resp_data:
                        logging.error(f"Subscription error: {resp_data['error']}")
                        if resp_data["error"].get("code") == -32007:  # Rate limit error
                            await asyncio.sleep(2)  # Wait before retrying
                            continue
                
                if not CLEAN_MODE:
                    print("Successfully subscribed to V2 and V3 events. Listening for new pairs/pools...")

                while True:
                    try:
                        message = await ws.recv()
                        event_data = json.loads(message)

                        if event_data.get("params") and event_data["params"].get("result"):
                            log = event_data["params"]["result"]
                            await rate_limiter.acquire()
                            
                            if log["address"].lower() == uniswap_v2_factory_address.lower():
                                await handle_v2_event(log)
                            elif log["address"].lower() == uniswap_v3_factory_address.lower():
                                await handle_v3_event(log)

                        elif "error" in event_data:
                            if event_data["error"].get("code") == -32007:  # Rate limit error
                                logging.warning("Rate limit hit, waiting...")
                                await asyncio.sleep(2)
                            else:
                                logging.error(f"WebSocket error: {event_data['error']}")

                    except websockets.exceptions.ConnectionClosed as e:
                        logging.error(f"Connection closed: {e}")
                        break

        except Exception as e:
            logging.error(f"Error in event listener: {e}")
            await asyncio.sleep(5)  # Wait before reconnecting
