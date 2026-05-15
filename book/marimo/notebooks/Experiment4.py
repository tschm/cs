# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo==0.23.1",
#     "numpy==2.4.4",
#     "plotly==6.7.0",
#     "polars==1.39.3",
#     "jquantstats==0.8.2",
#     "tinycta==0.12.0"
# ]
# ///

"""Experiment 4: CTA strategy with optimization and risk scaling.

This module demonstrates a more advanced trend-following strategy that
incorporates portfolio optimization techniques and risk scaling to
improve performance and risk-adjusted returns.
"""

import marimo

__generated_with = "0.23.1"
app = marimo.App()

with app.setup:
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import plotly.io as pio
    import polars as pl

    from jquantstats import Portfolio, interpolate

    # Ensure Plotly works with Marimo
    pio.renderers.default = "plotly_mimetype"

    path = Path(__file__).parent / "public" / "Prices_hashed.csv"

    date_col = "date"

    dframe = pl.read_csv(str(path), try_parse_dates=True)

    dframe = dframe.with_columns(pl.col(date_col).cast(pl.Datetime("ns")))
    dframe = dframe.with_columns([pl.col(col).cast(pl.Float64) for col in dframe.columns if col != date_col])
    prices = interpolate(dframe)


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
    import pandas as pd

    def returns_adjust(price, com=32, min_periods=300, clip=4.2):
        r = price.apply(np.log).diff()
        return (r / r.ewm(com=com, min_periods=min_periods).std()).clip(-clip, +clip)

    def osc_fn(prices, fast=32, slow=96):
        diff = prices.ewm(com=fast - 1).mean() - prices.ewm(com=slow - 1).mean()
        s = diff.std()
        return diff / s

    return osc_fn, pd, returns_adjust


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
def _(fast, osc_fn, pd, returns_adjust, slow, vola, winsor):
    assets = [c for c in prices.columns if c != date_col]
    prices_pd = pd.DataFrame(
        prices.drop(date_col).to_numpy(allow_copy=True),
        index=prices[date_col].to_list(),
        columns=assets,
    )

    mu = np.tanh(
        prices_pd.apply(returns_adjust, com=vola.value, clip=winsor.value)
        .cumsum()
        .apply(osc_fn, fast=fast.value, slow=slow.value)
    )
    volax = prices_pd.pct_change().ewm(com=vola.value, min_periods=vola.value).std()

    euclid_norm = np.sqrt((mu * mu).sum(axis=1))
    risk_scaled = mu.apply(lambda x: x / euclid_norm, axis=0)

    pos_np = np.nan_to_num((5e5 * risk_scaled / volax).values, nan=0.0)
    pos = pl.DataFrame(
        {date_col: prices[date_col]}
        | {col: pos_np[:, i].tolist() for i, col in enumerate(assets)}
    )
    portfolio = Portfolio.from_cash_position(prices=prices, cash_position=pos, aum=1e8)
    _nav = portfolio.nav_accumulated["NAV_accumulated"].pct_change().drop_nulls()
    print(float(_nav.mean() / _nav.std(ddof=1) * portfolio.data._periods_per_year**0.5))
    return (portfolio,)


@app.cell
def _(portfolio):
    fig = portfolio.plots.snapshot()
    fig
    return


if __name__ == "__main__":
    app.run()
