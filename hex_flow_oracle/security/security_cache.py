from time import time
import asyncio
from web3 import Web3
from ..security.token_security import check_token_security

class SecurityCache:
    def __init__(self, ttl=3600, max_size=1000):
        self.cache = {}
        self.ttl = ttl
        self.max_size = max_size

    async def get_or_check(self, token_address: str):
        now = time()
        if token_address in self.cache:
            result, timestamp = self.cache[token_address]
            if now - timestamp < self.ttl:
                return result
        
        result = await check_token_security(token_address)
        self.cache[token_address] = (result, now)
        return result

    async def cleanup(self):
        """Remove expired entries and trim cache size"""
        now = time()
        # Remove expired entries
        self.cache = {
            k: (v, t) for k, (v, t) in self.cache.items()
            if now - t < self.ttl
        }
        # Trim size if needed
        if len(self.cache) > self.max_size:
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
            self.cache = dict(sorted_items[-self.max_size:])
            
    async def _fetch_security_info(self, addresses):
        """Fetch security info for multiple addresses"""
        tasks = [check_token_security(addr) for addr in addresses]
        return await asyncio.gather(*tasks)

    async def batch_check(self, token_addresses):
        """Check multiple tokens at once"""
        # Use map with lambda to transform addresses
        checksum_addresses = list(map(lambda addr: Web3.to_checksum_address(addr), token_addresses))
        
        # Use filter with lambda to find uncached tokens
        uncached = list(filter(lambda addr: addr not in self.cache, checksum_addresses))
        
        # Fetch uncached tokens
        if uncached:
            results = await self._fetch_security_info(uncached)
            
            # Use lambda in dictionary comprehension
            self.cache.update({
                addr: (result, time()) 
                for addr, result in zip(uncached, results)
            })
            
        # Return all results
        return {addr: self.cache[addr][0] for addr in checksum_addresses} 