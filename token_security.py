from goplus.token import Token
import asyncio
from functools import lru_cache
from time import time

# Initialize Token checker, add access token if needed
token_checker = Token(access_token=None)

async def check_token_security(token_address):
    """Make token security check non-blocking"""
    try:
        # Run blocking API call in thread pool
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: token_checker.token_security(
                chain_id="1",
                addresses=[token_address],
                **{"_request_timeout": 10}
            )
        )
        data_str = str(response)
        return "'trust_list': '1'" in data_str or is_token_safe(data_str)
    except Exception as e:
        return False

def is_token_safe(data_str):
    safety_criteria = [
        "'is_honeypot': '0'",
        "'is_blacklisted': '0'",
        "'can_take_back_ownership': '0'",
        "'cannot_buy': '0'",
        "'cannot_sell_all': '0'",
        "'personal_slippage_modifiable': '0'",
        "'slippage_modifiable': '0'",
        "'sell_tax': '0'",
        "'buy_tax': '0'",
        "'is_airdrop_scam': '0'",
        "'is_proxy': '0'",
        "'trading_cooldown': '0'",
        "'transfer_pausable': '0'",
        "'is_in_dex': '1'"
    ]

    for criterion in safety_criteria:
        if criterion not in data_str:
            return False

    return True

async def batch_check_token_security(tokens: list[str], batch_size=5):
    """Process token security checks in batches"""
    results = {}
    for i in range(0, len(tokens), batch_size):
        batch = tokens[i:i + batch_size]
        tasks = [check_token_security(token) for token in batch]
        batch_results = await asyncio.gather(*tasks)
        results.update(dict(zip(batch, batch_results)))
    return results

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
