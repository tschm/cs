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

"""Experiment 2: Improved CTA strategy with volatility scaling.

This module enhances the basic trend-following strategy by incorporating
volatility scaling to adjust position sizes based on market conditions.
"""

import marimo

__generated_with = "0.23.1"
app = marimo.App()

with app.setup:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))

    from preamble import Portfolio, interpolate, load_prices, mo, pio, pl

    prices = load_prices(__file__)


@app.cell(hide_code=True)
def _():
    mo.md(r"""# CTA 2.0""")
    return



@app.function
def f(price: "pl.Expr", fast=32, slow=96, volatility=32) -> "pl.Expr":
    return (price.ewm_mean(com=fast, min_samples=300) - price.ewm_mean(com=slow, min_samples=300)).sign() / price.pct_change().ewm_std(com=volatility, min_samples=300)


@app.cell
def _():
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast Moving Average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow Moving Average")
    vola = mo.ui.slider(4, 192, step=4, value=32, label="Volatility")

    mo.vstack([fast, slow, vola])

    return fast, slow, vola


@app.cell
def _(fast, slow, vola):
    portfolio = Portfolio.from_cash_position(
        prices=prices,
        cash_position=(
            f(
                pl.all().exclude(date_col),
                fast=fast.value,
                slow=slow.value,
                volatility=vola.value,
            ).fill_null(0.0)
            * 1e5
        ),
        aum=1e8,
    )
    _nav = portfolio.nav_accumulated["NAV_accumulated"].pct_change().drop_nulls()
    print(float(_nav.mean() / _nav.std(ddof=1) * portfolio.data._periods_per_year**0.5))
    return (portfolio,)


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    * This is a **univariate** trading system, we map the (real) price of an asset to its (cash)position
    * Only 3 **free parameters** used here.
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
