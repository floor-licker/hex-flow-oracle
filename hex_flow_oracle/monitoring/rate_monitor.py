from tqdm import tqdm
import asyncio
import time
from collections import deque

class RateMonitor:
    def __init__(self, window_size=1.0, 
                 alert_threshold=lambda rate: rate > 12,
                 format_description=lambda rate: f"QuickNode Subscription Attempts/sec ({rate}/15)"):
        self.window_size = window_size
        self.requests = deque()
        self.alert_threshold = alert_threshold
        self.format_description = format_description
        self.pbar = tqdm(
            total=15,
            desc=format_description(0),
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
        self.pbar.set_description(self.format_description(current_rate))
        
        # Check alert threshold using lambda
        if self.alert_threshold(current_rate):
            self.pbar.colour = 'red'
        else:
            self.pbar.colour = 'green'
            
        self.pbar.refresh()

    async def monitor_loop(self):
        """Continuously update the display"""
        while True:
            self._update_display()
            await asyncio.sleep(0.1)

    def close(self):
        self.pbar.close() 