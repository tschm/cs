# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo==0.13.15",
#     "numpy==2.3.0",
#     "pandas==2.3.0",
#     "plotly==6.1.2",
#     "polars==1.30.0",
#     "cvxsimulator==1.4.3"
# ]
# ///

"""Experiment 2: Improved CTA strategy with volatility scaling.

This module enhances the basic trend-following strategy by incorporating
volatility scaling to adjust position sizes based on market conditions.
"""

import marimo

__generated_with = "0.13.15"
app = marimo.App()

with app.setup:
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.io as pio
    import polars as pl
    from cvxsimulator import interpolate

    # Ensure Plotly works with Marimo
    pio.renderers.default = "plotly_mimetype"
    pd.options.plotting.backend = "plotly"

    path = Path(__file__).parent / "public" / "Prices_hashed.csv"

    date_col = "date"

    dframe = pl.read_csv(str(path), try_parse_dates=True)

    dframe = dframe.with_columns(pl.col(date_col).cast(pl.Datetime("ns")))
    dframe = dframe.with_columns([pl.col(col).cast(pl.Float64) for col in dframe.columns if col != date_col])
    prices = dframe.to_pandas().set_index(date_col).apply(interpolate)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# CTA 2.0""")
    return


@app.cell
def _():
    import warnings

    # Suppress noisy warnings
    warnings.simplefilter(action="ignore", category=FutureWarning)
    return


@app.function
def f(price, fast=32, slow=96, volatility=32):
    """Calculate volatility-scaled trading signals based on moving averages.

    Args:
        price: Price series data
        fast: Fast moving average period (default: 32)
        slow: Slow moving average period (default: 96)
        volatility: Lookback period for volatility calculation (default: 32)

    Returns:
        Series of trading signals scaled by inverse volatility, providing
        larger positions during low volatility periods and smaller positions
        during high volatility periods
    """
    s = price.ewm(com=slow, min_periods=300).mean()
    f = price.ewm(com=fast, min_periods=300).mean()
    std = price.pct_change().ewm(com=volatility, min_periods=300).std()
    return np.sign(f - s) / std


@app.cell
def _():
    # Create sliders using marimo's UI components
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast Moving Average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow Moving Average")
    vola = mo.ui.slider(4, 192, step=4, value=32, label="Volatility")

    # Display the sliders in a vertical stack
    mo.vstack([fast, slow, vola])

    return fast, slow, vola


@app.cell
def _(f, fast, prices, slow, vola):
    from cvxsimulator import Portfolio

    pos = 1e5 * f(prices, fast=fast.value, slow=slow.value, volatility=vola.value)
    portfolio = Portfolio.from_cashpos_prices(prices=prices, cashposition=pos, aum=1e8)
    print(portfolio.sharpe())
    return (portfolio,)


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    * This is a **univariate** trading system, we map the (real) price of an asset to its (cash)position
    * Only 3 **free parameters** used here.
    * Only 4 lines of code
    * Scaling the bet-size by volatility has improved the situation.
    """
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    Results do not look terrible but...
    * No concept of risk integrated

    Often hedge funds outsource the risk management to some board or committee
    and develop machinery for more systematic **parameter-hacking**.
    """
    )
    return


@app.cell
def _(portfolio):
    portfolio.snapshot()
    return


if __name__ == "__main__":
    app.run()
