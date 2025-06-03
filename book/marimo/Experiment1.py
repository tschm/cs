import marimo

__generated_with = "0.13.14"
app = marimo.App(layout_file="layouts/notebook.slides.json")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# CTA 1.0""")
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import plotly.io as pio

    # Ensure Plotly works with Marimo
    pio.renderers.default = "plotly_mimetype"
    return mo, np, pd


@app.cell
def _():
    # Optional: import simulation modules
    from cvx.simulator import interpolate, Portfolio

    return Portfolio, interpolate


@app.cell
def _(mo, interpolate, pd):
    # Load prices
    prices = pd.read_csv(
        mo.notebook_location() / "data" / "Prices_hashed.csv", index_col=0, parse_dates=True
    )

    # interpolate the prices
    prices = prices.apply(interpolate)
    return (prices,)


@app.cell
def _(np):
    # take two moving averages and apply sign-functiond
    def f(price, fast=32, slow=96):
        s = price.ewm(com=slow, min_periods=100).mean()
        f = price.ewm(com=fast, min_periods=100).mean()
        return np.sign(f - s)

    return (f,)


@app.cell
def _(mo):
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast moving average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow moving average")

    mo.vstack([fast, slow])

    return fast, slow


@app.cell
def _(f, fast, prices, slow):
    pos = 5e6 * prices.apply(f, fast=fast.value, slow=slow.value).fillna(0.0)
    return (pos,)


@app.cell
def _(Portfolio, pos, prices):
    # builder = Builder(prices=prices, initial_aum=1e8)

    # for t, state in builder:
    #    # update the position
    #    position = pos.loc[t[-1]]
    #    builder.cashposition = position[state.assets].values
    #    # Do not apply trading costs
    #    builder.aum = state.aum

    # portfolio = builder.build()

    portfolio = Portfolio.from_cashpos_prices(prices=prices, cashposition=pos, aum=1e8)
    return (portfolio,)


@app.cell(hide_code=True)
def _(mo):
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
def _(mo):
    mo.md(
        r"""Such fundamental flaws are not addressed by **parameter-hacking** or **pimp-my-trading-system** steps (remove the worst performing assets, insane quantity of stop-loss limits, ...)"""
    )
    return


@app.cell
def _(portfolio):
    fig = portfolio.snapshot()
    fig
    return


@app.cell
def _(pd):
    pd.set_option("display.precision", 2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    cvxSimulator can construct portfolio objects. Those objects will expose functionality and attributes supporting all analytics.
    There are two types of portfolio -- EquityPortfolio and FuturesPortfolio. We start with the FuturesPortfolio. The most simple use-case
    is when we have computed all desirec cash-positions
    """
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
