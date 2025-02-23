from web3 import Web3

quicknode_ws_url = "wss://frequent-broken-smoke.quiknode.pro/9eb6428ae8ecb819e78a6ab9596f4ddce0b145c9"

# Factory Addresses - Ethereum Mainnet
NETWORK = "mainnet"  # Options: "mainnet", "goerli", "arbitrum", "optimism", "polygon"

FACTORY_ADDRESSES = {
    "mainnet": {
        "v2": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        "v3": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    },
    "goerli": {
        "v2": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        "v3": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    },
    "arbitrum": {
        "v3": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    },
    "optimism": {
        "v3": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    },
    "polygon": {
        "v2": "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
        "v3": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    }
}

# Set active factory addresses based on network
uniswap_v2_factory_address = Web3.to_checksum_address(FACTORY_ADDRESSES[NETWORK]["v2"])
uniswap_v3_factory_address = Web3.to_checksum_address(FACTORY_ADDRESSES[NETWORK]["v3"])

# Event Topics (same across all networks)
v2_pair_created_topic = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
v3_pool_created_topic = "0x783cca1c0412dd0d695e784568c96da2087fba7ca78f2288a3f1f3100f367fc8"

CLEAN_MODE = False  # Set to True for clean mode, False for normal mode
