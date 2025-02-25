from typing import Dict, Callable, Awaitable, Any

class AddressLookup:
    def __init__(self, address_map: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]]):
        self.address_map = address_map

    async def route_event(self, log):
        # Convert to string before calling lower()
        address = str(log["address"]).lower()
        handler = self.address_map.get(address)
        if handler:
            await handler(log) 