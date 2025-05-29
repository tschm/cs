import marimo

__generated_with = "0.13.14"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # CTA 4.0 - Optimization 1.0
        """
    )
    return


@app.cell
def _():
    import warnings

    import pandas as pd
    import numpy as np

    from cvx.simulator import Portfolio
    from cvx.simulator import interpolate

    from tinycta.signal import osc, returns_adjust

    warnings.simplefilter(action="ignore", category=FutureWarning)
    return Portfolio, interpolate, np, osc, pd, returns_adjust


@app.cell
def _(interpolate, pd):
    # Load prices
    prices = pd.read_csv("data/Prices_hashed.csv", index_col=0, parse_dates=True)

    # interpolate the prices
    prices = prices.apply(interpolate)
    return (prices,)


@app.cell
def _():
    from ipywidgets import Label, HBox, VBox, IntSlider, FloatSlider

    fast = IntSlider(min=4, max=192, step=4, value=32)
    slow = IntSlider(min=4, max=192, step=4, value=96)
    vola = IntSlider(min=4, max=192, step=4, value=32)
    winsor = FloatSlider(min=1.0, max=6.0, step=0.1, value=4.2)
    left_box = VBox(
        [
            Label("Fast Moving Average"),
            Label("Slow Moving Average"),
            Label("Volatility"),
            Label("Winsorizing"),
        ]
    )
    right_box = VBox([fast, slow, vola, winsor])
    HBox([left_box, right_box])
    return fast, slow, vola, winsor


@app.cell
def _(Portfolio, fast, np, osc, prices, returns_adjust, slow, vola, winsor):
    mu = np.tanh(
        prices.apply(returns_adjust, com=vola.value, clip=winsor.value)
        .cumsum()
        .apply(osc, fast=fast.value, slow=slow.value)
    )
    volax = prices.pct_change().ewm(com=vola.value, min_periods=vola.value).std()

    # compute the series of Euclidean norms by compute the sum of squares for each row
    euclid_norm = np.sqrt((mu * mu).sum(axis=1))

    # Divide each column of mu by the Euclidean norm
    risk_scaled = mu.apply(lambda x: x / euclid_norm, axis=0)

    pos = 5e5 * risk_scaled / volax
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
