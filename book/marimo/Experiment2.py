import marimo

__generated_with = "0.13.15"
app = marimo.App()


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


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.io as pio

    # Ensure Plotly works with Marimo
    pio.renderers.default = "plotly_mimetype"
    return mo, np, pd


@app.cell
def _():
    # Optional: import simulation modules
    from cvx.simulator import Portfolio, interpolate

    return Portfolio, interpolate


@app.cell
def _(interpolate, mo, pd):
    # Load prices
    prices = pd.read_csv(
        mo.notebook_location() / "public" / "Prices_hashed.csv",
        index_col=0,
        parse_dates=True,
    )

    # interpolate the prices
    prices = prices.apply(interpolate)
    return (prices,)


@app.cell
def _(np):
    # take two moving averages and apply the sign-function, adjust by volatility
    def f(price, fast=32, slow=96, volatility=32):
        s = price.ewm(com=slow, min_periods=300).mean()
        f = price.ewm(com=fast, min_periods=300).mean()
        std = price.pct_change().ewm(com=volatility, min_periods=300).std()
        return np.sign(f - s) / std

    return (f,)


@app.cell
def _(mo):
    # Create sliders using marimo's UI components
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast Moving Average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow Moving Average")
    vola = mo.ui.slider(4, 192, step=4, value=32, label="Volatility")

    # Display the sliders in a vertical stack
    mo.vstack([fast, slow, vola])

    return fast, slow, vola


@app.cell
def _(Portfolio, f, fast, prices, slow, vola):
    pos = 1e5 * f(prices, fast=fast.value, slow=slow.value, volatility=vola.value)
    portfolio = Portfolio.from_cashpos_prices(prices=prices, cashposition=pos, aum=1e8)
    return (portfolio,)


@app.cell(hide_code=True)
def _(mo):
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
def _(mo):
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
