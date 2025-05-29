import marimo

__generated_with = "0.13.14"
app = marimo.App(layout_file="layouts/notebook.slides.json")


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
    from cvx.simulator import Portfolio
    from cvx.simulator import interpolate

    from tinycta.signal import osc, returns_adjust

    return Portfolio, interpolate, osc, returns_adjust


@app.cell
def _(path, interpolate, pd):
    # Load prices
    prices = pd.read_csv(
        path / "data" / "Prices_hashed.csv", index_col=0, parse_dates=True
    )

    # interpolate the prices
    prices = prices.apply(interpolate)
    return (prices,)


@app.cell
def _(mo):
    # Create sliders using marimo's UI components
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast Moving Average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow Moving Average")
    vola = mo.ui.slider(4, 192, step=4, value=32, label="Volatility")
    winsor = mo.ui.slider(1.0, 6.0, step=0.1, value=4.2, label="Winsorizing")

    # Display the sliders in a vertical stack
    mo.vstack([fast, slow, vola, winsor])

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
    fig = portfolio.snapshot()
    fig
    return


if __name__ == "__main__":
    app.run()
