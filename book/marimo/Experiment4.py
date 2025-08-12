# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo==0.13.15",
#     "numpy==2.3.0",
#     "pandas==2.3.0",
#     "plotly==6.1.2",
#     "polars==1.30.0",
#     "cvxsimulator==1.4.3"
# ]
# ///

"""Experiment 4: CTA strategy with optimization and risk scaling.

This module demonstrates a more advanced trend-following strategy that
incorporates portfolio optimization techniques and risk scaling to
improve performance and risk-adjusted returns.
"""

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

    path = mo.notebook_location() / "public" / "Prices_hashed.csv"
    date_col = "date"

    dframe = pl.read_csv(str(path), try_parse_dates=True)

    dframe = dframe.with_columns(pl.col(date_col).cast(pl.Datetime("ns")))
    dframe = dframe.with_columns([pl.col(col).cast(pl.Float64) for col in dframe.columns if col != date_col])
    prices = dframe.to_pandas().set_index(date_col).apply(interpolate)


@app.cell(hide_code=True)
def _():
    mo.md(r"""# CTA 4.0 - Optimization 1.0""")
    return


@app.cell
def _():
    import warnings

    # Suppress noisy warnings
    warnings.simplefilter(action="ignore", category=FutureWarning)
    return


@app.cell
def _():
    from tinycta.signal import osc, returns_adjust

    return osc, returns_adjust


@app.cell
def _():
    # Create sliders using marimo's UI components
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast Moving Average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow Moving Average")
    vola = mo.ui.slider(4, 192, step=4, value=32, label="Volatility")
    winsor = mo.ui.slider(1.0, 6.0, step=0.1, value=4.2, label="Winsorizing")

    # Display the sliders in a vertical stack
    mo.vstack([fast, slow, vola, winsor])

    return fast, slow, vola, winsor


@app.cell
def _(fast, osc, returns_adjust, slow, vola, winsor):
    from cvxsimulator import Portfolio

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
    print(portfolio.sharpe())
    return (portfolio,)


@app.cell
def _(portfolio):
    fig = portfolio.snapshot()
    fig
    return


if __name__ == "__main__":
    app.run()
