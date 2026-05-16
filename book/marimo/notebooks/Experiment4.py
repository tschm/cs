# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo==0.23.1",
#     "numpy==2.4.4",
#     "plotly==6.7.0",
#     "polars==1.39.3",
#     "jquantstats==0.8.3",
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
    import sys
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import polars as pl
    from jquantstats import Portfolio
    from tinycta.osc import osc
    from tinycta.util import vol_adj

    sys.path.insert(0, str(Path(__file__).parent))

    from preamble import date_col, load_prices

    prices = load_prices(__file__)
    prices_only = prices.drop(date_col)
    assets = prices_only.columns


@app.cell(hide_code=True)
def _():
    mo.md(r"""# CTA 4.0 - Optimization 1.0""")
    return


@app.function
def f(price: "pl.Expr", fast=32, slow=96, vola=32, clip=4.2) -> "pl.Expr":
    return osc(vol_adj(price, vola=vola, clip=clip, min_samples=300).cum_sum(), fast=fast, slow=slow).tanh()


@app.cell
def _():
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast Moving Average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow Moving Average")
    vola = mo.ui.slider(4, 192, step=4, value=32, label="Volatility")
    winsor = mo.ui.slider(1.0, 6.0, step=0.1, value=4.2, label="Winsorizing")

    mo.vstack([fast, slow, vola, winsor])

    return fast, slow, vola, winsor


@app.cell
def _(fast, slow, vola, winsor):
    mu_np = prices_only.select(f(pl.all(), fast=fast.value, slow=slow.value, vola=vola.value, clip=winsor.value)).to_numpy()
    volax_np = prices_only.select(pl.all().fill_nan(None).pct_change().ewm_std(com=vola.value, min_samples=vola.value)).to_numpy()
    euclid_norm = np.sqrt(np.nansum(mu_np ** 2, axis=1, keepdims=True))
    euclid_norm[euclid_norm == 0] = np.nan
    risk_scaled_np = mu_np / euclid_norm

    pos_np = np.nan_to_num(5e5 * risk_scaled_np / volax_np, nan=0.0)
    portfolio = Portfolio.from_cash_position(
        prices=prices,
        cash_position=pl.concat([
            prices.select(date_col),
            pl.from_numpy(pos_np, schema=dict.fromkeys(assets, pl.Float64))
        ], how="horizontal"),
        aum=1e8,
    )
    return (portfolio,)


@app.cell
def _(portfolio):
    _r = portfolio.returns["returns"]
    print(float(_r.mean() / _r.std(ddof=1) * portfolio.data._periods_per_year**0.5))


@app.cell
def _(portfolio):
    fig = portfolio.plots.snapshot()
    fig
    return


if __name__ == "__main__":
    app.run()
