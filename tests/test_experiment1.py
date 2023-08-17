"""test portfolio"""
from __future__ import annotations

import numpy as np
import pytest

from tinycta.port import build_portfolio


# take two moving averages and apply sign-function
def f(prices, fast=32, slow=96):
    """
    construct cash position
    """
    s = prices.ewm(com=slow, min_periods=100).mean()
    f = prices.ewm(com=fast, min_periods=100).mean()
    return np.sign(f - s)


def test_portfolio(prices):
    """
    test portfolio

    Args:
        prices: adjusted prices of futures
    """
    portfolio = build_portfolio(prices=prices, cashposition=1e6 * f(prices))

    portfolio.metrics()["Sharpe"] == pytest.approx(0.5527420886866333)
