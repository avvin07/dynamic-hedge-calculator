# logic.py

import logging
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


def parse_float(value: str) -> float:
    """Parse a string into float, accepting both ',' and '.' as decimal separators."""
    try:
        return float(value.replace(',', '.'))
    except ValueError as e:
        logger.error(f"parse_float: cannot convert '{value}' to float: {e}")
        raise


def calculate_liquidity(current_price: float,
                        lower_bound: float,
                        upper_bound: float,
                        total_pool_value: float) -> float:
    """
    Calculate Uniswap V3 liquidity L for a symmetric LP range.

    Formula:
        L = V / ((1/√P_cur - 1/√P_high)·P_cur + (√P_cur - √P_low))
    """
    sqrt_cur = math.sqrt(current_price)
    sqrt_low = math.sqrt(lower_bound)
    sqrt_high = math.sqrt(upper_bound)
    denominator = ((1.0 / sqrt_cur - 1.0 / sqrt_high) * current_price
                   + (sqrt_cur - sqrt_low))
    if denominator == 0:
        logger.error("calculate_liquidity: denominator is zero")
        raise ZeroDivisionError("Invalid price bounds or current price")
    return total_pool_value / denominator


def position_amounts(liquidity: float,
                     price: float,
                     lower_bound: float,
                     upper_bound: float) -> tuple[float, float]:
    """
    Compute amounts of ETH and USDC in the position for a given price.

    Returns:
        (eth_amount, usdc_amount)
    """
    if price < lower_bound:
        eth = liquidity * (1.0 / math.sqrt(lower_bound) - 1.0 / math.sqrt(upper_bound))
        usdc = 0.0
    elif price > upper_bound:
        eth = 0.0
        usdc = liquidity * (math.sqrt(upper_bound) - math.sqrt(lower_bound))
    else:
        eth = liquidity * (1.0 / math.sqrt(price) - 1.0 / math.sqrt(upper_bound))
        usdc = liquidity * (math.sqrt(price) - math.sqrt(lower_bound))
    return eth, usdc


def calculate_hedge_fee(amount: float,
                        price: float,
                        fee_percent: float) -> float:
    """
    Calculate fee in USDC for a hedge transaction.

    Args:
        amount: amount of ETH to hedge (abs value)
        price: price at which hedge is executed
        fee_percent: fee percent (e.g. 0.2 for 0.2%)
    """
    return abs(amount) * price * (fee_percent / 100.0)


@dataclass
class HedgeTransaction:
    """
    Represents a single hedge transaction in grid or dynamic hedging.
    """
    price: float
    amount: float
    direction: str
    fee: float
    order_number: int

if __name__ == "__main__":
    import pytest
    pytest.main([__file__]) 