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
    from tinycta.linalg import inv_a_norm, solve
    from tinycta.signal import shrink2id

    def returns_adjust(price: "pl.DataFrame", com=32, min_periods=300, clip=4.2) -> "pl.DataFrame":
        cols = price.columns
        r = price.with_columns([pl.col(c).log().diff().fill_nan(None) for c in cols])
        std = r.with_columns([pl.col(c).ewm_std(com=com, min_samples=min_periods) for c in cols])
        return pl.DataFrame({c: (r[c] / std[c]).fill_nan(None).clip(-clip, clip) for c in cols})

    def osc_fn(prices: "pl.DataFrame", fast=32, slow=96) -> "pl.DataFrame":
        cols = prices.columns
        fast_ma = prices.with_columns([pl.col(c).ewm_mean(com=fast - 1) for c in cols])
        slow_ma = prices.with_columns([pl.col(c).ewm_mean(com=slow - 1) for c in cols])
        diff = pl.DataFrame({c: (fast_ma[c] - slow_ma[c]).fill_nan(None) for c in cols})
        return pl.DataFrame({c: diff[c] / diff[c].std() for c in cols})

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
    assets = [c for c in prices.columns if c != date_col]
    n_assets = len(assets)
    prices_only = prices.drop(date_col)
    n_rows = len(prices_only)
    correlation = corr.value

    returns_adj = returns_adjust(prices_only, com=vola.value, clip=winsor.value)

    # EWM correlation (DCC by Engle)
    # cov_t(i,j) = ewm_t(r_i * r_j) - ewm_t(r_i) * ewm_t(r_j)
    ewm_means_np = returns_adj.select([
        pl.col(c).ewm_mean(com=correlation, min_samples=int(correlation)) for c in assets
    ]).to_numpy()

    pair_indices = [(i, j) for i in range(n_assets) for j in range(i, n_assets)]
    ewm_prod_np = returns_adj.select([
        (pl.col(assets[i]) * pl.col(assets[j])).fill_nan(None)
        .ewm_mean(com=correlation, min_samples=int(correlation))
        .alias(f"p{i}_{j}")
        for i, j in pair_indices
    ]).to_numpy()

    cov_np = np.full((n_rows, n_assets, n_assets), np.nan)
    for _k, (_i, _j) in enumerate(pair_indices):
        _cov = ewm_prod_np[:, _k] - ewm_means_np[:, _i] * ewm_means_np[:, _j]
        cov_np[:, _i, _j] = _cov
        cov_np[:, _j, _i] = _cov

    _var = cov_np[:, np.arange(n_assets), np.arange(n_assets)]
    with np.errstate(invalid="ignore", divide="ignore"):
        _denom = np.sqrt(_var[:, :, None] * _var[:, None, :])
        cor_3d = cov_np / _denom
    for _k in range(n_assets):
        cor_3d[_var[:, _k] > 0, _k, _k] = 1.0

    adj_cs = returns_adj.with_columns([pl.col(c).fill_nan(None).cum_sum() for c in assets])
    osc_df = osc_fn(adj_cs)
    mu = osc_df.with_columns([pl.col(c).fill_nan(None).tanh() for c in osc_df.columns]).to_numpy()
    vo = prices_only.with_columns([
        pl.col(c).fill_nan(None).pct_change().ewm_std(com=vola.value, min_samples=int(vola.value))
        for c in assets
    ]).to_numpy()

    prices_np = prices_only.to_numpy()
    pos_matrix = np.zeros((n_rows, n_assets))

    for _n in range(n_rows):
        _mask = np.isfinite(prices_np[_n])
        if _mask.sum() == 0:
            continue
        _full_shrunk = shrink2id(cor_3d[_n], lamb=shrinkage.value)
        _matrix = _full_shrunk[_mask, :][:, _mask]
        _expected_mu = np.nan_to_num(mu[_n][_mask])
        _expected_vo = np.nan_to_num(vo[_n][_mask])
        _norm = inv_a_norm(_expected_mu, _matrix)
        if _norm == 0 or np.isnan(_norm):
            continue
        _risk_pos = solve(_matrix, _expected_mu) / _norm
        pos_matrix[_n, _mask] = np.nan_to_num(1e6 * _risk_pos / _expected_vo, nan=0.0)

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
