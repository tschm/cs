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

"""Experiment 5: Advanced CTA strategy with correlation-based optimization.

This module implements a sophisticated trend-following strategy that
incorporates dynamic conditional correlation (DCC) and matrix optimization
techniques to improve portfolio construction and risk management.
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
    mo.md(r"""# CTA 5.0 - Optimization 2.0""")
    return


@app.cell
def _():
    import warnings

    # Suppress noisy warnings
    warnings.simplefilter(action="ignore", category=FutureWarning)
    return


@app.cell
def _():
    from tinycta.linalg import inv_a_norm, solve
    from tinycta.signal import shrink2id

    def returns_adjust(price, com=32, min_periods=300, clip=4.2):
        r = price.apply(np.log).diff()
        return (r / r.ewm(com=com, min_periods=min_periods).std()).clip(-clip, +clip)

    def osc_fn(prices, fast=32, slow=96):
        diff = prices.ewm(com=fast - 1).mean() - prices.ewm(com=slow - 1).mean()
        s = diff.std()
        return diff / s

    return inv_a_norm, osc_fn, returns_adjust, shrink2id, solve


@app.cell
def _():
    # Create sliders using marimo's UI components
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast Moving Average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow Moving Average")
    vola = mo.ui.slider(4, 192, step=4, value=32, label="Volatility")
    winsor = mo.ui.slider(1.0, 6.0, step=0.1, value=4.2, label="Winsorizing")
    corr = mo.ui.slider(50, 500, step=10, value=200, label="Correlation")
    shrinkage = mo.ui.slider(0.0, 1.0, step=0.05, value=0.5, label="Shrinkage")

    # Display the sliders in a vertical stack
    mo.vstack([fast, slow, vola, winsor, corr, shrinkage])

    return corr, shrinkage, vola, winsor


@app.cell
def _(
    corr,
    inv_a_norm,
    osc_fn,
    returns_adjust,
    shrink2id,
    shrinkage,
    solve,
    vola,
    winsor,
):
    import pandas as pd

    assets = [c for c in prices.columns if c != date_col]

    correlation = corr.value

    prices_pd = pd.DataFrame(
        prices.drop(date_col).to_numpy(allow_copy=True),
        index=prices[date_col].to_list(),
        columns=assets,
    )

    returns_adj = prices_pd.apply(returns_adjust, com=vola.value, clip=winsor.value)

    # DCC by Engle
    cor = returns_adj.ewm(com=correlation, min_periods=correlation).corr()

    mu = np.tanh(returns_adj.cumsum().apply(osc_fn)).values
    vo = prices_pd.pct_change().ewm(com=vola.value, min_periods=vola.value).std().values

    pos_matrix = np.zeros((len(prices_pd), len(assets)))

    for n in range(len(prices_pd)):
        t = prices_pd.index[n]
        # Use prices-only mask (matching cvxsimulator state.mask behavior)
        mask = np.isfinite(prices_pd.iloc[n].values)
        if mask.sum() == 0:
            continue
        # Shrink full matrix first, then extract submatrix for available assets
        full_shrunk = shrink2id(cor.loc[t].values, lamb=shrinkage.value)
        matrix = full_shrunk[mask, :][:, mask]
        expected_mu = np.nan_to_num(mu[n][mask])
        expected_vo = np.nan_to_num(vo[n][mask])
        norm = inv_a_norm(expected_mu, matrix)
        if norm == 0 or np.isnan(norm):
            continue
        risk_pos = solve(matrix, expected_mu) / norm
        pos_matrix[n, mask] = np.nan_to_num(1e6 * risk_pos / expected_vo, nan=0.0)

    pos = pl.DataFrame(
        {date_col: prices[date_col]}
        | {col: pos_matrix[:, i].tolist() for i, col in enumerate(assets)}
    )
    portfolio = Portfolio.from_cash_position(prices=prices, cash_position=pos, aum=1e8)
    _nav = portfolio.nav_accumulated["NAV_accumulated"].pct_change().drop_nulls()
    print(float(_nav.mean() / _nav.std(ddof=1) * portfolio.data._periods_per_year**0.5))
    return (portfolio,)


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    # Conclusions
    * Dramatic relativ improvements observable despite using the same signals as in previous Experiment.
    * Main difference here is to take advantage of cross-correlations in the risk measurement.
    * Possible to add constraints on individual assets or groups of them.
    * Possible to reflect trading costs in objective with regularization terms (Ridge, Lars, Elastic Nets, ...)
    """
    )
    return


@app.cell
def _(portfolio):
    portfolio.plots.snapshot()
    return


if __name__ == "__main__":
    app.run()
