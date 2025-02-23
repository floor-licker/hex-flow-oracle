from tqdm import tqdm
import asyncio
import time
from collections import deque
from datetime import datetime, timedelta

class RateMonitor:
    def __init__(self, window_size=1.0):
        self.window_size = window_size
        self.requests = deque()
        self.pbar = tqdm(
            total=15,
            desc="QuickNode Subscription Attempts/sec",  # More accurate description
            bar_format='{desc}: {n_fmt}/{total_fmt} |{bar}| {percentage:3.0f}% [{elapsed}<{remaining}]',
            mininterval=0.1,
            maxinterval=0.5,
            smoothing=0.3
        )
        self.last_update = time.time()

    def add_request(self):
        now = time.time()
        self.requests.append(now)
        self._update_display()

    def _update_display(self):
        now = time.time()
        cutoff = now - self.window_size
        
        # Remove old requests
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

        # Calculate current rate
        current_rate = len(self.requests)
        
        # Update progress bar with current rate
        self.pbar.n = current_rate
        self.pbar.set_description(f"QuickNode Subscription Attempts/sec ({current_rate}/15)")  # More specific
        self.pbar.refresh()

    async def monitor_loop(self):
        """Continuously update the display"""
        while True:
            self._update_display()
            await asyncio.sleep(0.1)  # Update 10 times per second

    def close(self):
        self.pbar.close() 