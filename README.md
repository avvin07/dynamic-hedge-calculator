# Uniswap V3 Calculator

A GUI application to calculate and visualize Uniswap V3 liquidity positions.

## Features

- Calculate liquidity, token amounts, and position values for Uniswap V3 positions
- Visualize how your position changes across the price range
- See the effects of price movements to upper and lower bounds
- Interactive graph showing ETH and USDC amounts at different prices

## Requirements

- Python 3.7 or higher
- Required packages listed in `requirements.txt`

## Installation

1. Clone or download this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
python uniswap_v3_calc.py
```

2. Enter your desired parameters:
   - Current price (ETH)
   - Lower bound (USDC)
   - Upper bound (USDC)
   - Total pool value (USDC)

3. Click the "Calculate" button to update results and visualizations

4. View the calculated values for:
   - Current position (liquidity, ETH, USDC)
   - Position at upper bound
   - Position at lower bound

5. Examine the graph to see how your position changes with price movements

## Calculations

The application uses the Uniswap V3 formulas to calculate:

- Liquidity (L) = Total Pool Value / (((1/√P - 1/√Pb) * P) + (√P - √Pa))
  - Where P = current price, Pa = lower bound, Pb = upper bound

- Amount of ETH = L * (1/√P - 1/√Pb)
- Amount of USDC = L * (√P - √Pa)

- At upper bound (P = Pb), ETH = 0 and USDC = (√Pb - √P) * L + Amount of USDC at current price
- At lower bound (P = Pa), ETH = (√P - √Pa) * L / Pa + Amount of ETH at current price and USDC = 0 