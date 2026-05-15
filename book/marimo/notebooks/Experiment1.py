# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo==0.23.1",
#     "numpy==2.4.4",
#     "plotly==6.7.0",
#     "polars==1.39.3",
#     "jquantstats==0.8.2"
# ]
# ///

"""Experiment 1: Basic CTA strategy implementation using moving averages.

This module demonstrates a simple trend-following strategy using exponential
moving averages with different lookback periods.
"""

import marimo

__generated_with = "0.23.1"
app = marimo.App()

with app.setup:
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import plotly.io as pio
    import polars as pl

    from jquantstats import Portfolio, interpolate

    # Ensure Plotly works with Marimo
    pio.renderers.default = "plotly_mimetype"

    path = Path(__file__).parent / "public" / "Prices_hashed.csv"

    date_col = "date"

    dframe = pl.read_csv(str(path), try_parse_dates=True)

    dframe = dframe.with_columns(pl.col(date_col).cast(pl.Datetime("ns")))
    dframe = dframe.with_columns([pl.col(col).cast(pl.Float64) for col in dframe.columns if col != date_col])
    prices = interpolate(dframe)


@app.cell(hide_code=True)
def _():
    mo.md(r"""# CTA 1.0""")
    return


@app.function
def f(price, fast=32, slow=96):
    """Calculate trading signals based on the difference between fast and slow moving averages.

    Args:
        price: Polars Series of price data
        fast: Fast moving average period (default: 32)
        slow: Slow moving average period (default: 96)

    Returns:
        Series of trading signals (-1, 0, or 1) based on the sign of the difference
        between fast and slow moving averages
    """
    s = price.ewm_mean(com=slow, min_samples=100)
    fast_ma = price.ewm_mean(com=fast, min_samples=100)
    return (fast_ma - s).sign()


@app.cell
def _():
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast moving average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow moving average")

    mo.vstack([fast, slow])

    return fast, slow


@app.cell
def _(fast, slow):
    pos = prices.with_columns(
        f(pl.all().exclude(date_col), fast=fast.value, slow=slow.value).fill_null(0.0) * 5e6
    )
    return (pos,)


@app.cell
def _(pos):
    portfolio = Portfolio.from_cash_position(prices=prices, cash_position=pos, aum=1e8)
    _nav = portfolio.nav_accumulated["NAV_accumulated"].pct_change().drop_nulls()
    print(float(_nav.mean() / _nav.std(ddof=1) * portfolio.data._periods_per_year**0.5))
    return (portfolio,)


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    Results do not look terrible but...
    * No concept of risk integrated.
    * The size of each bet is constant regardless of the underlying asset.
    * The system lost its mojo in 2009 and has never really recovered.
    * The sign function is very expensive to trade as position changes are too extreme.
    """
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    Such fundamental flaws are not addressed by **parameter-hacking**
    or **pimp-my-trading-system** steps (remove the worst performing assets,
    insane quantity of stop-loss limits, ...)
    """
    )
    return


@app.cell
def _(portfolio):
    fig = portfolio.plots.snapshot()
    fig
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    cvxSimulator can construct portfolio objects. Those objects will
    expose functionality and attributes supporting all analytics.
    There are two types of portfolio -- EquityPortfolio and FuturesPortfolio.
    We start with the FuturesPortfolio. The most simple use-case
    is when we have computed all desirec cash-positions
    """
    )
    return


if __name__ == "__main__":
    app.run()
