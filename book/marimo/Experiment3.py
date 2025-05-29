import marimo

__generated_with = "0.13.14"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # CTA 3.0
        """
    )
    return


@app.cell
def _():
    import warnings

    from pathlib import Path

    #
    path = Path(__file__).parent

    # Suppress noisy warnings
    warnings.simplefilter(action="ignore", category=FutureWarning)
    return (path,)


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
def _(interpolate, path, pd):
    # Load prices
    prices = pd.read_csv(
        path / "data" / "Prices_hashed.csv", index_col=0, parse_dates=True
    )

    # interpolate the prices
    prices = prices.apply(interpolate)
    return (prices,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        We use the system:
        $$\mathrm{CashPosition}=\frac{f(\mathrm{Price})}{\mathrm{Volatility(Returns)}}$$

        This is very problematic:
        * Prices may live on very different scales, hence trying to find a more universal function $f$ is almost impossible. The sign-function was a good choice as the results don't depend on the scale of the argument.
        * Price may come with all sorts of spikes/outliers/problems.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        We need a simple price filter process
        * We compute volatility-adjusted returns, filter them and compute prices from those returns.
        * Don't call it Winsorizing in Switzerland. We apply Huber functions.

        """
    )
    return


@app.cell
def _(np):
    def filter(price, volatility=32, clip=4.2, min_periods=300):
        r = np.log(price).diff()
        vola = r.ewm(com=volatility, min_periods=min_periods).std()
        price_adj = (r / vola).clip(-clip, clip).cumsum()
        return price_adj

    return (filter,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ### Oscillators
        * All prices are now following a standard arithmetic Brownian motion with std $1$.
        * What we want is the difference of two moving means (exponentially weighted) to have a constant std regardless of the two lengths.
        * An oscillator is the **scaled difference of two moving averages**.

        """
    )
    return


@app.function
def osc(prices, fast=32, slow=96, scaling=True):
    diff = prices.ewm(com=fast - 1).mean() - prices.ewm(com=slow - 1).mean()
    if scaling:
        # attention this formula is forward-looking
        s = diff.std()
        # you may want to use
        #   f,g = 1 - 1/fast, 1-1/slow
        #   s = np.sqrt(1.0 / (1 - f * f) - 2.0 / (1 - f * g) + 1.0 / (1 - g * g))
        # or a moving std
    else:
        s = 1

    return diff / s


@app.cell
def _(np, pd):
    from numpy.random import randn

    price = pd.Series(data=randn(100000)).cumsum()

    o = osc(price, 40, 200, scaling=True)
    print("The std for the oscillator (Should be close to 1.0):")
    print(np.std(o))
    return


@app.cell
def _(filter, np):
    # from pycta.signal import osc

    # take two moving averages and apply tanh
    def f(price, slow=96, fast=32, vola=96, clip=3):
        # construct a fake-price, those fake-prices have homescedastic returns
        price_adj = filter(price, volatility=vola, clip=clip)
        # compute mu
        mu = np.tanh(osc(price_adj, fast=fast, slow=slow))
        return mu / price.pct_change().ewm(com=slow, min_periods=300).std()

    return (f,)


@app.cell
def _():
    import marimo as mo

    # Create sliders using marimo's UI components
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast Moving Average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow Moving Average")
    vola = mo.ui.slider(4, 192, step=4, value=32, label="Volatility")
    winsor = mo.ui.slider(1.0, 6.0, step=0.1, value=4.2, label="Winsorizing")

    # Display the sliders in a vertical stack
    mo.ui.vstack([fast, slow, vola, winsor])

    return fast, slow, vola, winsor


@app.cell
def _(Portfolio, f, fast, prices, slow, vola, winsor):
    pos = 1e5 * f(
        prices, fast=fast.value, slow=slow.value, vola=vola.value, clip=winsor.value
    )
    portfolio = Portfolio.from_cashpos_prices(prices=prices, cashposition=pos, aum=1e8)
    return (portfolio,)


@app.cell
def _(portfolio):
    portfolio.snapshot()
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
