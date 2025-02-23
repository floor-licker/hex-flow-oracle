from numba import jit
import numpy as np

@jit(nopython=True)
def calculate_price_impact(amounts: np.ndarray, reserves: np.ndarray) -> float:
    """
    Calculate price impact of a trade using constant product formula.
    Uses Numba for fast numerical computation.
    
    Args:
        amounts: numpy array of token amounts
        reserves: numpy array of pool reserves
    Returns:
        float: price impact percentage
    """
    k = reserves[0] * reserves[1]
    new_reserves = reserves + amounts
    new_k = new_reserves[0] * new_reserves[1]
    
    return abs((new_k - k) / k * 100)

@jit(nopython=True)
def calculate_optimal_amounts(
    target_price: float,
    reserves: np.ndarray,
    max_slippage: float
) -> np.ndarray:
    """
    Calculate optimal trade amounts to achieve target price within slippage.
    JIT compiled for performance.
    """
    current_price = reserves[0] / reserves[1]
    diff = abs(target_price - current_price)
    
    # Binary search for optimal amounts
    left = 0
    right = min(reserves) * 0.5
    optimal = np.zeros(2)
    
    while left < right:
        mid = (left + right) / 2
        test_amounts = np.array([mid, mid * current_price])
        impact = calculate_price_impact(test_amounts, reserves)
        
        if impact <= max_slippage:
            optimal = test_amounts
            left = mid + 1
        else:
            right = mid - 1
            
    return optimal 