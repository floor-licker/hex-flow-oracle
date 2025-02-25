import asyncio
import json
import websockets
from datetime import datetime
import logging

from .core.async_utils import AsyncRetryContext, WeakCache
from .core.event_buffer import AsyncEventBuffer
from .core.rate_limiting import AdaptiveRateLimiter
from .monitoring.logging_setup import setup_logging
from .events.event_handlers import handle_v2_event, handle_v3_event
from .events.address_lookup import AddressLookup
from .security.security_cache import SecurityCache
from .config import (
    quicknode_ws_url,
    uniswap_v2_factory_address,
    uniswap_v3_factory_address,
    v2_pair_created_topic,
    v3_pool_created_topic,
    CLEAN_MODE
)

logger = setup_logging()

def create_app():
    # Create dependencies
    rate_limiter = AdaptiveRateLimiter(
        initial_rate=5,
        window_size=2.0,
        failure_threshold=2,
        recovery_timeout=120.0,
        adaptive_factor=0.3
    )
    
    security_cache = SecurityCache(ttl=3600, max_size=1000)
    event_buffer = AsyncEventBuffer(max_size=1000)
    
    # Create address lookup with handlers
    address_lookup = AddressLookup({
        str(uniswap_v2_factory_address).lower(): handle_v2_event,
        str(uniswap_v3_factory_address).lower(): handle_v3_event
    })
    
    return {
        'rate_limiter': rate_limiter,
        'security_cache': security_cache,
        'event_buffer': event_buffer,
        'address_lookup': address_lookup
    }

@AsyncRetryContext()
async def listen_for_pair_created_events():
    app = create_app()
    rate_limiter = app['rate_limiter']
    event_buffer = app['event_buffer']
    address_lookup = app['address_lookup']
    
    # Define event handlers using lambdas
    event_handlers = {
        str(uniswap_v2_factory_address).lower(): lambda log: handle_v2_event(log),
        str(uniswap_v3_factory_address).lower(): lambda log: handle_v3_event(log)
    }
    
    while True:
        try:
            # Add delay between connection attempts
            await asyncio.sleep(2)
            
            async with websockets.connect(quicknode_ws_url) as ws:
                # Combine subscriptions into one request
                subscription = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": [
                        "logs",
                        {
                            "address": [
                                uniswap_v2_factory_address,
                                uniswap_v3_factory_address
                            ],
                            "topics": [
                                [v2_pair_created_topic, v3_pool_created_topic]
                            ]
                        }
                    ]
                }

                while True:  # Retry loop for subscription
                    if not await rate_limiter.acquire():
                        await asyncio.sleep(5)
                        continue
                        
                    try:
                        await ws.send(json.dumps(subscription))
                        response = await ws.recv()
                        resp_data = json.loads(response)
                        
                        if "error" in resp_data:
                            rate_limiter._handle_failure()
                            if resp_data["error"].get("code") == -32007:
                                await asyncio.sleep(10)
                                continue
                            raise Exception(resp_data["error"])
                        
                        rate_limiter._handle_success()
                        break  # Successfully subscribed
                        
                    except Exception as e:
                        logger.error(f"Subscription attempt failed: {e}")
                        rate_limiter._handle_failure()
                        await asyncio.sleep(5)
                
                if not CLEAN_MODE:
                    logger.info("Successfully subscribed to V2 and V3 events. Listening for new pairs/pools...")

                # Event listening loop
                while True:
                    try:
                        message = await ws.recv()
                        event_data = json.loads(message)

                        if event_data.get("params") and event_data["params"].get("result"):
                            log = event_data["params"]["result"]
                            address = str(log["address"]).lower()
                            
                            # Use lambda for handler lookup and execution
                            handler = event_handlers.get(address)
                            if handler:
                                await handler(log)

                    except websockets.exceptions.ConnectionClosed as e:
                        logger.error(f"Connection closed: {e}")
                        break

        except Exception as e:
            logger.error(f"Error in event listener: {e}")
            rate_limiter._handle_failure()
            await asyncio.sleep(10)

async def main():
    await listen_for_pair_created_events()

if __name__ == "__main__":
    asyncio.run(main()) 