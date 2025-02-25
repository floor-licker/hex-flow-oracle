import json
from ..security.token_security import check_token_security
from ..config import CLEAN_MODE

async def handle_v2_event(log):
    """Handle V2 PairCreated event"""
    token0 = "0x" + log["topics"][1][26:]
    token1 = "0x" + log["topics"][2][26:]
    pair_address = "0x" + log["data"][26:66]
    
    token0_trusted = await check_token_security(token0)
    token1_trusted = await check_token_security(token1)
    
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
    
    token0_trusted = await check_token_security(token0)
    token1_trusted = await check_token_security(token1)
    
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