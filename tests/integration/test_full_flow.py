import pytest
from web3 import Web3
from eth_tester import EthereumTester
from eth_tester.backends.pyevm import PyEVMBackend

@pytest.fixture
def eth_tester():
    return EthereumTester(PyEVMBackend())

@pytest.mark.integration
async def test_pool_creation_detection(eth_tester):
    # Setup local blockchain
    w3 = Web3(Web3.EthereumTesterProvider(eth_tester))
    
    # Deploy test contracts
    # Monitor events
    # Verify detection 