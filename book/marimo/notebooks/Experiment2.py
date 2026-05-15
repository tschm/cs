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

"""Experiment 2: Improved CTA strategy with volatility scaling.

This module enhances the basic trend-following strategy by incorporating
volatility scaling to adjust position sizes based on market conditions.
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
def f(price: "pl.Expr", fast=32, slow=96, volatility=32) -> "pl.Expr":
    return (price.ewm_mean(com=fast, min_samples=300) - price.ewm_mean(com=slow, min_samples=300)).sign() / price.pct_change().ewm_std(com=volatility, min_samples=300)


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
def _(fast, slow, vola):
    pos = prices.with_columns(
        f(pl.all().exclude(date_col), fast=fast.value, slow=slow.value, volatility=vola.value).fill_null(0.0) * 1e5
    )
    portfolio = Portfolio.from_cash_position(prices=prices, cash_position=pos, aum=1e8)
    _nav = portfolio.nav_accumulated["NAV_accumulated"].pct_change().drop_nulls()
    print(float(_nav.mean() / _nav.std(ddof=1) * portfolio.data._periods_per_year**0.5))
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
    portfolio.plots.snapshot()
    return


if __name__ == "__main__":
    app.run()
