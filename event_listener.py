import asyncio
import json
import websockets
from config import quicknode_ws_url, uniswap_factory_address, pair_created_topic
from token_security import check_token_security

async def listen_for_pair_created_events():
    async with websockets.connect(quicknode_ws_url) as ws:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_subscribe",
            "params": [
                "logs",
                {
                    "address": uniswap_factory_address,
                    "topics": [pair_created_topic]
                }
            ]
        }
        await ws.send(json.dumps(payload))
        print("Subscribed to PairCreated events. Listening for new pairs...")

        while True:
            try:
                message = await ws.recv()
                event_data = json.loads(message)

                if event_data.get("params") and event_data["params"].get("result"):
                    log = event_data["params"]["result"]

                    token0 = "0x" + log["topics"][1][26:]
                    token1 = "0x" + log["topics"][2][26:]
                    pair_contract_address = "0x" + log["data"][26:66]

                    print("\nPairCreated event detected:")
                    print(f"Token 0: {token0}")
                    print(f"Token 1: {token1}")
                    print(f"Pair Contract Address: {pair_contract_address}")
                    print(json.dumps(log, indent=4))

                    check_token_security(token0)
                    check_token_security(token1)
                else:
                    print("Received heartbeat or other message:", message)
            except websockets.exceptions.ConnectionClosed as e:
                print(f"Connection closed with error: {e}. Reconnecting...")
                await asyncio.sleep(5)
                await listen_for_pair_created_events()
            except Exception as e:
                print(f"Error: {e}")
                break
