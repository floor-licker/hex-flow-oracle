![Alt text](images/cover-art.png)

# Hex-Flow Oracle: Advanced Liquidity Pool Monitoring System

A high-performance system for monitoring Uniswap V2/V3 liquidity pool deployments with sophisticated security validation and event processing capabilities.

## Key Features

- Real-time monitoring of Uniswap V2 and V3 pool creation events across multiple networks
- Advanced token security validation using GoPlus API
- Sophisticated event buffering with backpressure handling (1000+ events/second)
- Thread-safe caching system with weak references for optimal memory management
- Exponential backoff retry mechanism for robust error handling
- Multi-chain support (Ethereum, Arbitrum, Optimism, Polygon)
- Production-grade logging and monitoring
- Rate limiting with token bucket algorithm
- Concurrent validation of contract interfaces

## Supported Networks

- Ethereum Mainnet
- Goerli Testnet
- Arbitrum
- Optimism
- Polygon

## Technical Features

- Asynchronous WebSocket connections with connection pooling
- Memory-efficient event processing with backpressure handling
- Advanced caching system with TTL and size management
- Metaclass-based contract validation
- Generic type hints for type safety
- Comprehensive error handling and logging
- Configurable clean mode for production integration

## Setup Instructions

1. Create a QuickNode account and endpoint
2. Copy your QuickNode WSS Provider link into the config.py file
3. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Configure network and mode settings in config.py
5. Run the monitoring system:
   ```bash
   python main.py
   ```

## Integration Notes

Output of the program is sent to std::out in JSON format. For integration with trading applications, set CLEAN_MODE = True in config.py, this will ensure that no empty messages or heartbeats are ever sent, and the only output will be the hash values of secure and approved tokens of newly created liquidity pools.

## Advanced Usage

- Memory Management: The system uses weak references and automatic garbage collection
- Rate Limiting: Configurable rate limits with exponential backoff
- Event Buffering: Sophisticated event queue with backpressure handling
- Contract Validation: Automatic validation of contract interfaces
- Multi-Network Support: Easy configuration for different networks

## Performance Features

- Concurrent contract validation
- Efficient memory usage with weak references
- Automatic garbage collection
- Rate limiting with token bucket algorithm
- Event buffering with backpressure
- Connection pooling for WebSocket connections

Note that Github is currently experiencing bugs with users trying to access .pdf files embedded in repositories on Safari. If you wish to view the technical paper, please use an alternative browser such as Chrome.

[View Hex-Flow Oracle Technical Paper](docs/hex-flow-oracle-technical-paper.pdf)

## Technical Architecture

- Asynchronous event processing using Python's asyncio
- Thread-safe caching mechanisms
- Advanced error handling with retry logic
- Comprehensive logging system
- Type-safe implementations
- Memory-efficient data structures

## Security Features

- Token security validation
- Contract interface verification
- Rate limiting protection
- Error handling and logging
- Clean mode for production use

## Contributing

Please ensure all tests pass and add appropriate documentation for any new features.

