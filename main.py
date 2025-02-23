import asyncio
import aiohttp
import json
from web3 import Web3, AsyncWeb3
from event_listener import listen_for_pair_created_events
import signal
from config import NETWORK, FACTORY_ADDRESSES, quicknode_ws_url
import os
from functools import lru_cache

# RPC endpoints for different networks
RPC_URLS = {
    "mainnet": quicknode_ws_url.replace('wss://', 'https://'),  # Convert WebSocket URL to HTTPS
    "goerli": "https://eth-goerli.g.alchemy.com/v2/your-api-key",
    "arbitrum": "https://arb-mainnet.g.alchemy.com/v2/your-api-key",
    "optimism": "https://opt-mainnet.g.alchemy.com/v2/your-api-key",
    "polygon": "https://polygon-mainnet.g.alchemy.com/v2/your-api-key"
}

# Cache ABI loading to prevent repeated disk reads
@lru_cache(maxsize=None)
def load_abi(filename):
    """Load ABI from json file with caching"""
    with open(filename, 'r') as f:
        return json.load(f)

async def validate_factory_addresses():
    """Validate factory addresses by checking if they have contract code on-chain and expected functions."""
    print(f"Validating factory addresses for network: {NETWORK}")
    
    # Load ABIs (now cached)
    v2_abi = load_abi('uniswap_v2_factory_abi.json')
    v3_abi = load_abi('uniswap_v3_factory_abi.json')
    
    # Initialize AsyncWeb3 for better performance
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_URLS[NETWORK]))
    
    async def check_contract(address, version):
        """Check contract validity with concurrent function calls"""
        try:
            # Convert address once
            checksum_address = Web3.to_checksum_address(address)
            
            # Get contract code
            code = await w3.eth.get_code(checksum_address)
            if len(code) <= 2:
                return False, "No contract code found at address"
            
            # Create contract instance
            contract = w3.eth.contract(
                address=checksum_address,
                abi=v2_abi if version == "v2" else v3_abi
            )
            
            # Prepare all function calls concurrently
            if version == "v2":
                tasks = [
                    contract.functions.allPairsLength().call(),
                    contract.functions.feeTo().call()
                ]
            else:  # v3
                tasks = [
                    contract.functions.owner().call(),
                    contract.functions.feeAmountTickSpacing(3000).call()
                ]
            
            # Run all validation calls concurrently
            await asyncio.gather(*tasks)
            return True, "Contract validated successfully"
            
        except Exception as e:
            return False, f"Contract validation failed: {str(e)}"

    # Validate all addresses concurrently
    tasks = [
        check_contract(address, version) 
        for version, address in FACTORY_ADDRESSES[NETWORK].items()
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Process results
    for (version, address), (is_valid, message) in zip(
        FACTORY_ADDRESSES[NETWORK].items(), 
        results
    ):
        status = "✓ valid" if is_valid else f"✗ invalid: {message}"
        print(f"{version.upper()} Factory ({address}): {status}")
        
        if not is_valid:
            raise ValueError(
                f"Invalid {version.upper()} factory address on {NETWORK}: "
                f"{address}\nReason: {message}"
            )
    
    print("All factory addresses validated successfully!")
    return dict(zip(FACTORY_ADDRESSES[NETWORK].keys(), (r[0] for r in results)))

async def shutdown(signal, loop):
    """Cleanup tasks tied to the service's shutdown."""
    print(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    print(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

def handle_exception(loop, context):
    """Handle exceptions outside of coroutines."""
    msg = context.get("exception", context["message"])
    print(f"Caught exception: {msg}")

async def main():
    # Validate factory addresses before starting
    try:
        await validate_factory_addresses()
    except Exception as e:
        print(f"Factory validation failed: {e}")
        return
    
    # Start the event listener
    await listen_for_pair_created_events()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    
    # Handle exceptions
    loop.set_exception_handler(handle_exception)
    
    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(shutdown(s, loop))
        )
    
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
