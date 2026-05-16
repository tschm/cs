# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo==0.23.1",
#     "numpy==2.4.4",
#     "plotly==6.7.0",
#     "polars==1.39.3",
#     "jquantstats==0.8.3"
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
    import sys
    from pathlib import Path

    import marimo as mo
    import polars as pl
    from jquantstats import Portfolio

    sys.path.insert(0, str(Path(__file__).parent))

    from preamble import date_col, load_prices

    prices = load_prices(__file__)
    prices_only = prices.drop(date_col)


@app.cell(hide_code=True)
def _():
    mo.md(r"""# CTA 1.0""")
    return


@app.function
def f(price: "pl.Expr", fast=32, slow=96) -> "pl.Expr":
    return (price.ewm_mean(com=fast, min_samples=100) - price.ewm_mean(com=slow, min_samples=100)).sign()


@app.cell
def _():
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast moving average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow moving average")

    mo.vstack([fast, slow])

    return fast, slow


@app.cell
def _(fast, slow):
    signals = prices_only.select(f(pl.all(), fast=fast.value, slow=slow.value).fill_null(0.0) * 5e6)
    portfolio = Portfolio.from_cash_position(prices=prices, cash_position=signals, aum=1e8)
    return (portfolio,)


@app.cell
def _(portfolio):
    print(portfolio.stats.sharpe())


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



if __name__ == "__main__":
    app.run()
