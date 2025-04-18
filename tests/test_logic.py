import pytest
import math

from logic import parse_float, calculate_liquidity, position_amounts, calculate_hedge_fee


def test_parse_float_dot():
    assert parse_float("123.45") == pytest.approx(123.45)


def test_parse_float_comma():
    assert parse_float("123,45") == pytest.approx(123.45)


def test_parse_float_invalid():
    with pytest.raises(ValueError):
        parse_float("not a number")


def test_calculate_liquidity_normal():
    cp, lb, ub, val = 4.0, 1.0, 9.0, 100.0
    L = calculate_liquidity(cp, lb, ub, val)
    denom = ((1/math.sqrt(cp) - 1/math.sqrt(ub)) * cp + (math.sqrt(cp) - math.sqrt(lb)))
    assert L == pytest.approx(val / denom)


def test_calculate_liquidity_zero_denominator():
    # lower == current == upper leads to zero denominator
    with pytest.raises(ZeroDivisionError):
        calculate_liquidity(2.0, 2.0, 2.0, 100.0)


def test_position_amounts_below_lower():
    L, lb, ub, price = 100.0, 5.0, 10.0, 4.0
    eth, usdc = position_amounts(L, price, lb, ub)
    expected_eth = L * (1/math.sqrt(lb) - 1/math.sqrt(ub))
    assert eth == pytest.approx(expected_eth)
    assert usdc == pytest.approx(0.0)


def test_position_amounts_above_upper():
    L, lb, ub, price = 100.0, 5.0, 10.0, 12.0
    eth, usdc = position_amounts(L, price, lb, ub)
    expected_usdc = L * (math.sqrt(ub) - math.sqrt(lb))
    assert eth == pytest.approx(0.0)
    assert usdc == pytest.approx(expected_usdc)


def test_position_amounts_inside():
    L, lb, ub, price = 100.0, 5.0, 10.0, 7.0
    eth, usdc = position_amounts(L, price, lb, ub)
    expected_eth = L * (1/math.sqrt(price) - 1/math.sqrt(ub))
    expected_usdc = L * (math.sqrt(price) - math.sqrt(lb))
    assert eth == pytest.approx(expected_eth)
    assert usdc == pytest.approx(expected_usdc)


def test_calculate_hedge_fee_positive():
    fee = calculate_hedge_fee(2.0, 50.0, 0.2)
    assert fee == pytest.approx(2.0 * 50.0 * (0.2/100))


def test_calculate_hedge_fee_negative_amount():
    fee = calculate_hedge_fee(-3.0, 100.0, 0.5)
    assert fee == pytest.approx(3.0 * 100.0 * (0.5/100)) 