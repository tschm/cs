# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo==0.23.1",
#     "numpy==2.4.4",
#     "plotly==6.7.0",
#     "polars==1.39.3",
#     "jquantstats==0.8.2",
#     "tinycta==0.12.2"
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
    def returns_adjust(price: "pl.DataFrame", com=32, min_periods=300, clip=4.2) -> "pl.DataFrame":
        cols = price.columns
        # fill_nan converts float NaN (e.g. from log of negative prices) to null
        # so that ewm_std and cum_sum treat them as missing rather than propagating NaN
        r = price.with_columns([pl.col(c).log().diff().fill_nan(None) for c in cols])
        std = r.with_columns([pl.col(c).ewm_std(com=com, min_samples=min_periods) for c in cols])
        return pl.DataFrame({c: (r[c] / std[c]).fill_nan(None).clip(-clip, clip) for c in cols})

    def osc_fn(prices: "pl.DataFrame", fast=32, slow=96) -> "pl.DataFrame":
        cols = prices.columns
        fast_ma = prices.with_columns([pl.col(c).ewm_mean(com=fast - 1) for c in cols])
        slow_ma = prices.with_columns([pl.col(c).ewm_mean(com=slow - 1) for c in cols])
        diff = pl.DataFrame({c: (fast_ma[c] - slow_ma[c]).fill_nan(None) for c in cols})
        f, g = 1 - 1 / fast, 1 - 1 / slow
        s = np.sqrt(1.0 / (1 - f * f) - 2.0 / (1 - f * g) + 1.0 / (1 - g * g))
        return pl.DataFrame({c: diff[c] / s for c in cols})

    return osc_fn, returns_adjust


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
def _(fast, osc_fn, returns_adjust, slow, vola, winsor):
    assets = [c for c in prices.columns if c != date_col]
    prices_only = prices.drop(date_col)

    adj = returns_adjust(prices_only, com=vola.value, clip=winsor.value)
    adj_cs = adj.with_columns([pl.col(c).fill_nan(None).cum_sum() for c in adj.columns])
    osc_df = osc_fn(adj_cs, fast=fast.value, slow=slow.value)
    mu = osc_df.with_columns([pl.col(c).fill_nan(None).tanh() for c in osc_df.columns])

    volax = prices_only.with_columns([
        pl.col(c).fill_nan(None).pct_change().ewm_std(com=vola.value, min_samples=vola.value)
        for c in prices_only.columns
    ])

    mu_np = mu.to_numpy()
    volax_np = volax.to_numpy()
    # nansum matches pandas DataFrame.sum(axis=1, skipna=True): assets with no data
    # for a given row contribute 0 rather than propagating NaN into the norm
    euclid_norm = np.sqrt(np.nansum(mu_np ** 2, axis=1, keepdims=True))
    euclid_norm[euclid_norm == 0] = np.nan
    risk_scaled_np = mu_np / euclid_norm

    pos_np = np.nan_to_num(5e5 * risk_scaled_np / volax_np, nan=0.0)
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
