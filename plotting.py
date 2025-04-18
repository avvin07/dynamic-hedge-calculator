# plotting.py
"""
Module for plotting Uniswap V3 hedge calculator charts in a vectorized and reusable way.
"""
import numpy as np
import matplotlib.pyplot as plt
from logic import calculate_liquidity, position_amounts, calculate_hedge_fee


def plot_liquidity_range(ax1, ax2,
                         current_price: float,
                         lower_bound: float,
                         upper_bound: float,
                         total_pool_value: float,
                         num_points: int = 1000):
    """
    Plot liquidity range: ETH and USDC allocation and total value.
    """
    # Calculate price range
    price_min = lower_bound * 0.8
    price_max = upper_bound * 1.15
    prices = np.linspace(price_min, price_max, num_points)

    # Compute root prices
    sqrt_prices = np.sqrt(prices)
    sqrt_low = np.sqrt(lower_bound)
    sqrt_up = np.sqrt(upper_bound)

    # Calculate liquidity
    liquidity = calculate_liquidity(current_price, lower_bound, upper_bound, total_pool_value)

    # Vectorized positions
    eth = np.where(
        prices < lower_bound,
        liquidity * (1.0 / sqrt_low - 1.0 / sqrt_up),
        np.where(
            prices > upper_bound,
            0.0,
            liquidity * (1.0 / sqrt_prices - 1.0 / sqrt_up)
        )
    )

    usdc = np.where(
        prices < lower_bound,
        0.0,
        np.where(
            prices > upper_bound,
            liquidity * (sqrt_up - sqrt_low),
            liquidity * (sqrt_prices - sqrt_low)
        )
    )

    total = eth * prices + usdc

    # Plot ETH and USDC
    ax1.clear()
    ax1.plot(prices, eth, label='ETH', color='#1f77b4', linewidth=2)
    ax1.set_ylabel('ETH', color='#1f77b4')
    ax1.tick_params(axis='y', labelcolor='#1f77b4')

    ax1_right = ax1.twinx()
    ax1_right.plot(prices, usdc, label='USDC', color='#2ca02c', linewidth=2)
    ax1_right.set_ylabel('USDC', color='#2ca02c')
    ax1_right.tick_params(axis='y', labelcolor='#2ca02c')

    # Vertical lines
    for x, style in [(lower_bound, '--'), (upper_bound, '--'), (current_price, '-')]:
        ax1.axvline(x=x, color='gray', linestyle=style)
        ax1_right.axvline(x=x, color='gray', linestyle=style)

    ax1.set_xlim(price_min, price_max)
    ax1.set_title('ETH and USDC Allocation', fontsize=12)
    ax1.grid(True, alpha=0.3)

    # Plot total value
    ax2.clear()
    ax2.plot(prices, total, label='Total Value', color='#d62728', linewidth=2)
    ax2.axhline(y=total_pool_value, color='blue', linestyle='--', label='Initial Value')
    for x, style in [(lower_bound, '--'), (upper_bound, '--'), (current_price, '-')]:
        ax2.axvline(x=x, color='gray', linestyle=style)
    ax2.set_xlim(price_min, price_max)
    ax2.set_title('Total Position Value (USDC)', fontsize=12)
    ax2.set_xlabel('Price (USDC per ETH)')
    ax2.set_ylabel('Value (USDC)')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='best')


def plot_hedged_position(ax,
                         current_price: float,
                         lower_bound: float,
                         upper_bound: float,
                         total_pool_value: float,
                         hedge_amount: float,
                         hedge_price: float,
                         fee_percent: float,
                         num_points: int = 1000):
    """
    Plot comparison of base LP value and hedged strategy P&L.
    """
    price_min = lower_bound * 0.8
    price_max = upper_bound * 1.15
    prices = np.linspace(price_min, price_max, num_points)

    # Base position
    sqrt_prices = np.sqrt(prices)
    sqrt_low = np.sqrt(lower_bound)
    sqrt_up = np.sqrt(upper_bound)
    liquidity = calculate_liquidity(current_price, lower_bound, upper_bound, total_pool_value)
    eth = np.where(
        prices < lower_bound,
        liquidity * (1.0 / sqrt_low - 1.0 / sqrt_up),
        np.where(
            prices > upper_bound,
            0.0,
            liquidity * (1.0 / sqrt_prices - 1.0 / sqrt_up)
        )
    )
    usdc = np.where(
        prices < lower_bound,
        0.0,
        np.where(
            prices > upper_bound,
            liquidity * (sqrt_up - sqrt_low),
            liquidity * (sqrt_prices - sqrt_low)
        )
    )
    base_value = eth * prices + usdc

    # Hedge P&L
    fee = calculate_hedge_fee(hedge_amount, hedge_price, fee_percent)
    pnl_hedge = -hedge_amount * (prices - hedge_price) - fee
    hedged_value = base_value + pnl_hedge

    ax.clear()
    ax.plot(prices, base_value, label='Base LP (USDC)', color='#d62728', linewidth=2)
    ax.plot(prices, hedged_value, label='Hedged Strategy (USDC)', color='#2ca02c', linewidth=2)
    ax.plot(prices, total_pool_value + pnl_hedge, label='Hedge P&L (USDC)', color='#ff7f0e', alpha=0.4)
    ax.axhline(y=total_pool_value, color='blue', linestyle='--', label=f'Initial Pool ({total_pool_value} USDC)')

    # Lines for bounds and prices
    for x, style, color in [(lower_bound, '--', 'gray'),
                             (upper_bound, '--', 'gray'),
                             (current_price, '-', 'black'),
                             (hedge_price, ':', 'blue')]:
        ax.axvline(x=x, linestyle=style, color=color)

    ax.set_xlim(price_min, price_max)
    ax.set_xlabel('Price (USDC per ETH)')
    ax.set_ylabel('Value (USDC)')
    ax.set_title('Hedged vs Base LP P&L', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')


def plot_hedged_position_with_exit(ax,
                                   current_price: float,
                                   lower_bound: float,
                                   upper_bound: float,
                                   total_pool_value: float,
                                   hedge_amount: float,
                                   hedge_price: float,
                                   fee_percent: float,
                                   exit_price: float,
                                   num_points: int = 1000):
    """
    Plot hedged strategy with an exit price marker and annotations.
    """
    # First plot base and hedged curves
    plot_hedged_position(ax,
                         current_price,
                         lower_bound,
                         upper_bound,
                         total_pool_value,
                         hedge_amount,
                         hedge_price,
                         fee_percent,
                         num_points)

    # Add exit price line and annotation
    ax.axvline(x=exit_price, color='red', linestyle='-.', linewidth=2, label='Exit Price')
    # Расчёт значений в точке exit_price
    sqrt_low = np.sqrt(lower_bound)
    sqrt_up = np.sqrt(upper_bound)
    liquidity = calculate_liquidity(current_price, lower_bound, upper_bound, total_pool_value)
    # ETH/USDC в пуле на exit_price
    if exit_price < lower_bound:
        eth_exit = liquidity * (1.0 / sqrt_low - 1.0 / sqrt_up)
        usdc_exit = 0.0
    elif exit_price > upper_bound:
        eth_exit = 0.0
        usdc_exit = liquidity * (sqrt_up - sqrt_low)
    else:
        eth_exit = liquidity * (1.0 / np.sqrt(exit_price) - 1.0 / sqrt_up)
        usdc_exit = liquidity * (np.sqrt(exit_price) - sqrt_low)
    base_exit = eth_exit * exit_price + usdc_exit
    pnl_exit = -hedge_amount * (exit_price - hedge_price) - calculate_hedge_fee(hedge_amount, hedge_price, fee_percent)
    hedged_exit = base_exit + pnl_exit
    # Добавляем подписи
    ax.text(exit_price, base_exit, f"{base_exit:.0f}", color='#d62728', ha='left', va='bottom', fontsize=8)
    ax.text(exit_price, hedged_exit, f"{hedged_exit:.0f}", color='#2ca02c', ha='left', va='top', fontsize=8)
    ax.text(exit_price, total_pool_value + pnl_exit, f"{pnl_exit:.0f}", color='#ff7f0e', ha='left', va='bottom', fontsize=8)
    ax.legend(loc='best') 