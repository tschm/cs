# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo==0.23.14",
#     "numpy==2.4.6",
#     "plotly==6.9.0",
#     "polars==1.42.1",
#     "jquantstats==0.9.7",
#     "tinycta==0.13.3"
# ]
# ///

"""Experiment 5: Advanced CTA strategy with correlation-based optimization.

This module implements a sophisticated trend-following strategy that
incorporates dynamic conditional correlation (DCC) and matrix optimization
techniques to improve portfolio construction and risk management.
"""

import marimo

__generated_with = "0.23.9"
app = marimo.App()

with app.setup:
    import sys
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import polars as pl
    from jquantstats import Portfolio
    from tinycta.linalg import inv_a_norm, solve
    from tinycta.osc import osc
    from tinycta.signal import shrink2id
    from tinycta.util import vol_adj

    sys.path.insert(0, str(Path(__file__).parent))

    from preamble import date_col, load_prices

    prices = load_prices(__file__)
    prices_only = prices.drop(date_col)
    assets = prices_only.columns


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # CTA 5.0 - Optimization 2.0
    """)
    return


@app.function
def f(price: "pl.Expr", fast=32, slow=96, vola=32, clip=4.2) -> "pl.Expr":
    """Return the tanh oscillator of vol-adjusted cumulative price."""
    return osc(vol_adj(price, vola=vola, clip=clip, min_samples=300).cum_sum(), fast=fast, slow=slow).tanh()


@app.cell
def _():
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast Moving Average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow Moving Average")
    vola = mo.ui.slider(4, 192, step=4, value=32, label="Volatility")
    winsor = mo.ui.slider(1.0, 6.0, step=0.1, value=4.2, label="Winsorizing")
    corr = mo.ui.slider(50, 500, step=10, value=200, label="Correlation")
    shrinkage = mo.ui.slider(0.0, 1.0, step=0.05, value=0.5, label="Shrinkage")

    mo.vstack([fast, slow, vola, winsor, corr, shrinkage])
    return corr, shrinkage, vola, winsor


@app.function
def ewm_covariance(returns_adj: "pl.DataFrame", *, corr: int) -> "np.ndarray":
    """EWM covariance tensor of the vol-adjusted returns (the Engle-DCC numerator).

    ``cov_t(i, j) = ewm_t(r_i * r_j) - ewm_t(r_i) * ewm_t(r_j)``, evaluated for
    every day; the result has shape ``(n_rows, n_assets, n_assets)`` and is
    symmetric in ``(i, j)``.
    """
    columns = returns_adj.columns
    n_assets = len(columns)
    n_rows = len(returns_adj)

    ewm_means_np = returns_adj.select(pl.all().ewm_mean(com=corr, min_samples=int(corr))).to_numpy()

    pair_indices = [(i, j) for i in range(n_assets) for j in range(i, n_assets)]
    ewm_prod_np = returns_adj.select(
        [
            (pl.col(columns[i]) * pl.col(columns[j]))
            .fill_nan(None)
            .ewm_mean(com=corr, min_samples=int(corr))
            .alias(f"p{i}_{j}")
            for i, j in pair_indices
        ]
    ).to_numpy()

    cov_np = np.full((n_rows, n_assets, n_assets), np.nan)
    for _k, (_i, _j) in enumerate(pair_indices):
        _cov = ewm_prod_np[:, _k] - ewm_means_np[:, _i] * ewm_means_np[:, _j]
        cov_np[:, _i, _j] = _cov
        cov_np[:, _j, _i] = _cov
    return cov_np


@app.function
def correlation_from_covariance(cov_np: "np.ndarray") -> "np.ndarray":
    """Normalize a per-day covariance tensor to a correlation tensor.

    Days with non-positive variance keep their NaN off-diagonals; the diagonal
    is forced to 1 wherever the variance is positive.
    """
    n_assets = cov_np.shape[1]
    _var = cov_np[:, np.arange(n_assets), np.arange(n_assets)]
    with np.errstate(invalid="ignore", divide="ignore"):
        _denom = np.sqrt(_var[:, :, None] * _var[:, None, :])
        cor_3d = cov_np / _denom
    for _k in range(n_assets):
        cor_3d[_var[:, _k] > 0, _k, _k] = 1.0
    return cor_3d


@app.function
def dcc_correlation(prices_only: "pl.DataFrame", *, vola: int, clip: float, corr: int) -> "np.ndarray":
    """Engle-DCC per-day correlation tensor, shape ``(n_rows, n_assets, n_assets)``."""
    returns_adj = prices_only.select(vol_adj(pl.all(), vola=vola, clip=clip, min_samples=300))
    cov_np = ewm_covariance(returns_adj, corr=corr)
    return correlation_from_covariance(cov_np)


@app.function
def positions(
    cor_3d: "np.ndarray", mu: "np.ndarray", vo: "np.ndarray", prices_np: "np.ndarray", *, shrinkage: float
) -> "np.ndarray":
    """Per-day risk-parity positions from the shrunk DCC correlation tensor.

    Each day, the correlation matrix is shrunk towards the identity, restricted
    to the assets with a finite price, and used to solve for the risk-scaled
    position. Days with no live assets or a singular/zero norm are left flat.
    """
    n_rows, n_assets = prices_np.shape
    pos_matrix = np.zeros((n_rows, n_assets))
    for _n in range(n_rows):
        _mask = np.isfinite(prices_np[_n])
        if _mask.sum() == 0:
            continue
        _full_shrunk = shrink2id(cor_3d[_n], lamb=shrinkage)
        _matrix = _full_shrunk[_mask, :][:, _mask]
        _expected_mu = np.nan_to_num(mu[_n][_mask])
        _expected_vo = np.nan_to_num(vo[_n][_mask])
        _norm = inv_a_norm(_expected_mu, _matrix)
        if _norm == 0 or np.isnan(_norm):
            continue
        _risk_pos = solve(_matrix, _expected_mu) / _norm
        pos_matrix[_n, _mask] = np.nan_to_num(1e6 * _risk_pos / _expected_vo, nan=0.0)
    return pos_matrix


@app.cell
def _(corr, shrinkage, vola, winsor):
    # EWM correlation (DCC by Engle), then per-day risk-parity positions.
    cor_3d = dcc_correlation(prices_only, vola=vola.value, clip=winsor.value, corr=corr.value)

    mu = prices_only.select(f(pl.all(), fast=32, slow=96, vola=vola.value, clip=winsor.value)).to_numpy()
    vo = prices_only.select(
        pl.all().fill_nan(None).pct_change().ewm_std(com=vola.value, min_samples=int(vola.value))
    ).to_numpy()

    pos_matrix = positions(cor_3d, mu, vo, prices_only.to_numpy(), shrinkage=shrinkage.value)

    portfolio = Portfolio.from_cash_position(
        prices=prices,
        cash_position=pl.concat(
            [prices.select(date_col), pl.from_numpy(pos_matrix, schema=dict.fromkeys(assets, pl.Float64))],
            how="horizontal_extend",
        ),
        aum=1e8,
    )
    return (portfolio,)


@app.cell
def _(portfolio):
    print(portfolio.stats.sharpe())
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Conclusions
    * Dramatic relative improvements observable despite using the same signals as in previous Experiment.
    * Main difference here is to take advantage of cross-correlations in the risk measurement.
    * Possible to add constraints on individual assets or groups of them.
    * Possible to reflect trading costs in objective with regularization terms (Ridge, Lars, Elastic Nets, ...)
    """)
    return


@app.cell
def _(portfolio):
    portfolio.plots.snapshot()
    return


@app.cell
def _(portfolio):
    portfolio.stats.summary()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
