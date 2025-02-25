import asyncio
from asyncio import Queue
import logging
from typing import List, Dict, Any

class EventProcessor:
    def __init__(self, address_lookup):
        self.queue = Queue()
        self.batch_size = 10
        self.batch_timeout = 1.0
        self.address_lookup = address_lookup

    async def process_batch(self, batch: List[Dict[str, Any]]):
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