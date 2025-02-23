from hypothesis import given, strategies as st
from token_security import SecurityCache

@given(st.lists(st.text(min_size=42, max_size=42)))
def test_security_cache_properties(addresses):
    cache = SecurityCache(max_size=1000)
    
    # Property: Cache should never exceed max size
    for addr in addresses:
        cache.get_or_check(addr)
        assert len(cache.cache) <= cache.max_size 