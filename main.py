import asyncio
from event_listener import listen_for_pair_created_events

if __name__ == "__main__":
    asyncio.run(listen_for_pair_created_events())
