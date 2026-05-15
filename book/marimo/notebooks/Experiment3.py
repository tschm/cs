# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo==0.23.1",
#     "numpy==2.4.4",
#     "plotly==6.7.0",
#     "polars==1.39.3",
#     "jquantstats==0.8.3",
#     "tinycta==0.12.2"
# ]
# ///

"""Experiment 3: Advanced CTA strategy with price filtering and oscillators.

This module implements a more sophisticated trend-following strategy that
incorporates price filtering to handle outliers and oscillators with proper
scaling for more consistent signal generation across different assets.
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
    from tinycta.osc import osc
    from tinycta.util import vol_adj

    sys.path.insert(0, str(Path(__file__).parent))

    from preamble import date_col, load_prices

    prices = load_prices(__file__)
    prices_only = prices.drop(date_col)


@app.cell(hide_code=True)
def _():
    mo.md(r"""# CTA 3.0""")
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    We use the system:
    $$\mathrm{CashPosition}=\frac{f(\mathrm{Price})}{\mathrm{Volatility(Returns)}}$$

    This is very problematic:
    * Prices may live on very different scales, hence trying to find a
    more universal function $f$ is almost impossible. The sign-function was
    a good choice as the results don't depend on the scale of the argument.
    * Price may come with all sorts of spikes/outliers/problems.
    """
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    We need a simple price filter process
    * We compute volatility-adjusted returns, filter them and compute prices from those returns.
    * Don't call it Winsorizing in Switzerland. We apply Huber functions.
    """
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    ### Oscillators
    * All prices are now following a standard arithmetic Brownian
    motion with std $1$.
    * What we want is the difference of two moving means (exponentially weighted)
    to have a constant std regardless of the two lengths.
    * An oscillator is the **scaled difference of two moving averages**.
    """
    )
    return


@app.function
def f(price: "pl.Expr", slow=96, fast=32, vola=96, clip=3) -> "pl.Expr":
    price_adj = vol_adj(price, vola=vola, clip=clip, min_samples=300).cum_sum()
    mu = osc(price_adj, fast=fast, slow=slow).tanh()
    vol = price.pct_change().ewm_std(com=slow, min_samples=300)
    return mu / vol


@app.cell
def _():
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast Moving Average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow Moving Average")
    vola = mo.ui.slider(4, 192, step=4, value=32, label="Volatility")
    winsor = mo.ui.slider(1.0, 6.0, step=0.1, value=4.2, label="Winsorizing")

    mo.vstack([fast, slow, vola, winsor])

    return fast, slow, vola, winsor


@app.cell
def _(fast, slow, vola, winsor):
    signals = prices_only.select(
        (f(pl.all(), fast=fast.value, slow=slow.value, vola=vola.value, clip=winsor.value) * 1e5)
        .fill_nan(0.0).fill_null(0.0)
    )
    portfolio = Portfolio.from_cash_position(prices=prices, cash_position=signals, aum=1e8)
    return (portfolio,)


@app.cell
def _(portfolio):
    _nav = portfolio.nav_accumulated["NAV_accumulated"].pct_change().drop_nulls()
    print(float(_nav.mean() / _nav.std(ddof=1) * portfolio.data._periods_per_year**0.5))


@app.cell
def _(portfolio):
    fig = portfolio.plots.snapshot()
    fig
    return


if __name__ == "__main__":
    app.run()
