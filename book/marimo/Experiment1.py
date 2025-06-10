import marimo

__generated_with = "0.13.15"
app = marimo.App()

with app.setup:
    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.io as pio
    import polars as pl
    from cvxsimulator import interpolate

    # Ensure Plotly works with Marimo
    pio.renderers.default = "plotly_mimetype"
    pd.options.plotting.backend = "plotly"

    price_file = mo.notebook_location() / "public" / "Prices_hashed.csv"
    prices_pl = pl.read_csv(str(price_file), try_parse_dates=True)
    prices_pd = prices_pl.to_pandas().set_index("date")


@app.cell(hide_code=True)
def _():
    mo.md(r"""# CTA 1.0""")
    return


@app.cell
def _():
    # this cell should be made obsolete by the Simulator accepting polar frames
    # from cvx.simulator import interpolate
    # from cvx.simulator.builder import polars2pandas

    # print(prices_pl)
    # prices = polars2pandas(prices_pl)

    # interpolate the prices
    prices = prices_pd.apply(interpolate)
    # print(prices)
    # return
    return prices


@app.function
# take two moving averages and apply sign-functiond
def f(price, fast=32, slow=96):
    s = price.ewm(com=slow, min_periods=100).mean()
    f = price.ewm(com=fast, min_periods=100).mean()
    return np.sign(f - s)


@app.cell
def _():
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast moving average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow moving average")

    mo.vstack([fast, slow])

    return fast, slow


@app.cell
def _(fast, slow, prices):
    pos = 5e6 * prices.apply(f, fast=fast.value, slow=slow.value).fillna(0.0)
    return (pos,)


@app.cell
def _(pos, prices):
    from cvxsimulator import Portfolio
    # builder = Builder(prices=prices, initial_aum=1e8)

    # for t, state in builder:
    #    # update the position
    #    position = pos.loc[t[-1]]
    #    builder.cashposition = position[state.assets].values
    #    # Do not apply trading costs
    #    builder.aum = state.aum

    # portfolio = builder.build()

    # interpolate the prices inside here...
    portfolio = Portfolio.from_cashpos_prices(prices=prices, cashposition=pos, aum=1e8)
    print(portfolio.sharpe())
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
    fig = portfolio.snapshot()
    fig


@app.cell
def _():
    pd.set_option("display.precision", 2)


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
