"""Optuna parameter optimization for the CTA experiments.

Each ``ExperimentN.py`` marimo notebook defines a signal function ``f(...)`` and
builds a :class:`jquantstats.Portfolio` whose Sharpe ratio is the quantity the
notebook's sliders are meant to tune by hand. This module replays the exact same
portfolio construction (reusing each notebook's ``f`` and the TinyCTA API) and
hands the search over to `Optuna <https://optuna.org>`_, maximizing the
portfolio Sharpe ratio over each experiment's parameter space.

Run from the command line::

    python optimize.py --experiment 3 --trials 200
    python optimize.py --experiment all

The signal functions are imported from the notebooks via :func:`runpy.run_path`
(the same mechanism the tests use), so this stays a single source of truth: the
strategy logic lives in the notebooks, the search space lives here.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import numpy as np
import optuna
import polars as pl
from jquantstats import Portfolio
from tinycta.linalg import inv_a_norm, solve
from tinycta.signal import shrink2id

NOTEBOOK_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(NOTEBOOK_DIR))

from preamble import date_col, load_notebook, load_prices  # noqa: E402

# ── Data and signal functions (loaded once) ──────────────────────────────────

PRICES = load_prices(str(NOTEBOOK_DIR / "optimize.py"))
PRICES_ONLY = PRICES.drop(date_col)
ASSETS = PRICES_ONLY.columns

# ``clip`` is a fixed winsorizing level, not a search dimension.
CLIP = 4.2


def _signal(notebook: str) -> Callable[..., Any]:
    """Import the signal function ``f`` from an experiment notebook."""
    return cast("Callable[..., Any]", load_notebook(notebook)["f"])


F1 = _signal("Experiment1.py")
F2 = _signal("Experiment2.py")
F3 = _signal("Experiment3.py")
F4 = _signal("Experiment4.py")
F5 = _signal("Experiment5.py")


def _sharpe(portfolio: Portfolio) -> float:
    """Return the portfolio's annualized Sharpe ratio (the optimization target)."""
    value = portfolio.stats.sharpe()["returns"]
    return float(value) if np.isfinite(value) else float("-inf")


# ── Portfolio builders (one per experiment, mirroring each notebook cell) ─────


def build_exp1(*, fast: int, slow: int) -> Portfolio:
    """CTA 1.0 — sign of the fast-minus-slow EWM crossover."""
    signals = PRICES_ONLY.select(F1(pl.all(), fast=fast, slow=slow).fill_null(0.0) * 5e6)
    return Portfolio.from_cash_position(prices=PRICES, cash_position=signals, aum=1e8)


def build_exp2(*, fast: int, slow: int, volatility: int) -> Portfolio:
    """CTA 2.0 — volatility-scaled crossover."""
    signals = PRICES_ONLY.select(F2(pl.all(), fast=fast, slow=slow, volatility=volatility).fill_null(0.0) * 1e5)
    return Portfolio.from_cash_position(prices=PRICES, cash_position=signals, aum=1e8)


def build_exp3(*, fast: int, slow: int, vola: int, clip: float) -> Portfolio:
    """CTA 3.0 — tanh oscillator on vol-adjusted prices, divided by volatility."""
    signals = PRICES_ONLY.select(
        (F3(pl.all(), fast=fast, slow=slow, vola=vola, clip=clip) * 1e5).fill_nan(0.0).fill_null(0.0)
    )
    return Portfolio.from_cash_position(prices=PRICES, cash_position=signals, aum=1e8)


def build_exp4(*, fast: int, slow: int, vola: int, clip: float) -> Portfolio:
    """CTA 4.0 — Euclidean risk-scaling across assets (optimization 1.0)."""
    mu_np = PRICES_ONLY.select(F4(pl.all(), fast=fast, slow=slow, vola=vola, clip=clip)).to_numpy()
    volax_np = PRICES_ONLY.select(pl.all().fill_nan(None).pct_change().ewm_std(com=vola, min_samples=vola)).to_numpy()
    euclid_norm = np.sqrt(np.nansum(mu_np**2, axis=1, keepdims=True))
    euclid_norm[euclid_norm == 0] = np.nan
    risk_scaled_np = mu_np / euclid_norm
    pos_np = np.nan_to_num(5e5 * risk_scaled_np / volax_np, nan=0.0)
    return _portfolio_from_matrix(pos_np)


def build_exp5(*, vola: int, clip: float, corr: int, shrinkage: float) -> Portfolio:
    """CTA 5.0 — DCC correlation + shrinkage matrix optimization (optimization 2.0).

    ``fast``/``slow`` are held at the notebook's fixed 32/96 — the notebook only
    exposes vola, clip, corr and shrinkage to the search.
    """
    from tinycta.util import vol_adj

    n_assets = len(ASSETS)
    n_rows = len(PRICES_ONLY)

    returns_adj = PRICES_ONLY.select(vol_adj(pl.all(), vola=vola, clip=clip, min_samples=300))

    # EWM correlation (DCC by Engle):
    # cov_t(i,j) = ewm_t(r_i * r_j) - ewm_t(r_i) * ewm_t(r_j)
    ewm_means_np = returns_adj.select(pl.all().ewm_mean(com=corr, min_samples=int(corr))).to_numpy()

    pair_indices = [(i, j) for i in range(n_assets) for j in range(i, n_assets)]
    ewm_prod_np = returns_adj.select(
        [
            (pl.col(ASSETS[i]) * pl.col(ASSETS[j]))
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

    _var = cov_np[:, np.arange(n_assets), np.arange(n_assets)]
    with np.errstate(invalid="ignore", divide="ignore"):
        _denom = np.sqrt(_var[:, :, None] * _var[:, None, :])
        cor_3d = cov_np / _denom
    for _k in range(n_assets):
        cor_3d[_var[:, _k] > 0, _k, _k] = 1.0

    mu = PRICES_ONLY.select(F5(pl.all(), fast=32, slow=96, vola=vola, clip=clip)).to_numpy()
    vo = PRICES_ONLY.select(pl.all().fill_nan(None).pct_change().ewm_std(com=vola, min_samples=int(vola))).to_numpy()

    prices_np = PRICES_ONLY.to_numpy()
    pos_matrix = np.zeros((n_rows, n_assets))

    # The search deliberately explores (corr, shrinkage) regions that make the
    # daily correlation matrix ill-conditioned or singular; the guards below
    # handle the degenerate days, so silence the accompanying numerical noise.
    # (TinyCTA's ``SingularMatrixError`` is a ``ValueError``; the conditioning
    # warning is matched by message to avoid importing cvx's internal classes.)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Matrix condition number")
        warnings.filterwarnings("ignore", category=RuntimeWarning, message="invalid value encountered in sqrt")
        for _n in range(n_rows):
            _mask = np.isfinite(prices_np[_n])
            if _mask.sum() == 0:
                continue
            _full_shrunk = shrink2id(cor_3d[_n], lamb=shrinkage)
            _matrix = _full_shrunk[_mask, :][:, _mask]
            _expected_mu = np.nan_to_num(mu[_n][_mask])
            _expected_vo = np.nan_to_num(vo[_n][_mask])
            try:
                _norm = inv_a_norm(_expected_mu, _matrix)
            except ValueError:
                # Singular correlation matrix on this day (some corr/shrinkage
                # combinations trigger it); skip the day rather than the trial.
                continue
            if _norm == 0 or np.isnan(_norm):
                continue
            _risk_pos = solve(_matrix, _expected_mu) / _norm
            pos_matrix[_n, _mask] = np.nan_to_num(1e6 * _risk_pos / _expected_vo, nan=0.0)

    return _portfolio_from_matrix(pos_matrix)


def _portfolio_from_matrix(pos_np: np.ndarray) -> Portfolio:
    """Wrap a (rows x assets) position matrix into a Portfolio with the date column."""
    cash_position = pl.concat(
        [PRICES.select(date_col), pl.from_numpy(pos_np, schema=dict.fromkeys(ASSETS, pl.Float64))],
        how="horizontal",
    )
    return Portfolio.from_cash_position(prices=PRICES, cash_position=cash_position, aum=1e8)


# ── Optuna search spaces ──────────────────────────────────────────────────────
#
# ``fast``/``slow``/``vola`` ranges mirror the marimo sliders (4..192 step 4).
# ``clip`` is held fixed at ``CLIP`` (4.2) rather than searched. ``slow`` is drawn
# strictly above ``fast`` so the oscillator stays well-defined (osc requires
# fast < slow) and the crossover keeps its fast/slow meaning.


def _suggest_fast_slow(trial: optuna.Trial) -> tuple[int, int]:
    """Sample a (fast, slow) pair with slow strictly above fast."""
    fast = trial.suggest_int("fast", 4, 96, step=4)
    slow = trial.suggest_int("slow", fast + 4, 192, step=4)
    return fast, slow


def objective_exp1(trial: optuna.Trial) -> float:
    """Sharpe of CTA 1.0 for a sampled (fast, slow)."""
    fast, slow = _suggest_fast_slow(trial)
    return _sharpe(build_exp1(fast=fast, slow=slow))


def objective_exp2(trial: optuna.Trial) -> float:
    """Sharpe of CTA 2.0 for a sampled (fast, slow, volatility)."""
    fast, slow = _suggest_fast_slow(trial)
    volatility = trial.suggest_int("volatility", 4, 192, step=4)
    return _sharpe(build_exp2(fast=fast, slow=slow, volatility=volatility))


def objective_exp3(trial: optuna.Trial) -> float:
    """Sharpe of CTA 3.0 for a sampled (fast, slow, vola); clip is fixed."""
    fast, slow = _suggest_fast_slow(trial)
    vola = trial.suggest_int("vola", 4, 192, step=4)
    return _sharpe(build_exp3(fast=fast, slow=slow, vola=vola, clip=CLIP))


def objective_exp4(trial: optuna.Trial) -> float:
    """Sharpe of CTA 4.0 for a sampled (fast, slow, vola); clip is fixed."""
    fast, slow = _suggest_fast_slow(trial)
    vola = trial.suggest_int("vola", 4, 192, step=4)
    return _sharpe(build_exp4(fast=fast, slow=slow, vola=vola, clip=CLIP))


def objective_exp5(trial: optuna.Trial) -> float:
    """Sharpe of CTA 5.0 for a sampled (vola, corr, shrinkage); clip is fixed."""
    vola = trial.suggest_int("vola", 4, 192, step=4)
    corr = trial.suggest_int("corr", 50, 500, step=10)
    shrinkage = trial.suggest_float("shrinkage", 0.0, 1.0, step=0.05)
    return _sharpe(build_exp5(vola=vola, clip=CLIP, corr=corr, shrinkage=shrinkage))


# ── Experiment registry ───────────────────────────────────────────────────────


class Experiment:
    """Bundles an objective with its baseline (notebook default) for reporting."""

    def __init__(
        self, name: str, objective: Callable[..., Any], default_params: dict[str, Any], baseline: Callable[..., Any]
    ):
        """Store the experiment's name, Optuna objective, notebook defaults and builder."""
        self.name = name
        self.objective = objective
        self.default_params = default_params
        self._baseline = baseline

    def default_sharpe(self) -> float:
        """Sharpe of the strategy run with the notebook's default (slider) parameters."""
        return _sharpe(self._baseline(**self.default_params))


EXPERIMENTS: dict[str, Experiment] = {
    "1": Experiment("Experiment 1", objective_exp1, {"fast": 32, "slow": 96}, build_exp1),
    "2": Experiment("Experiment 2", objective_exp2, {"fast": 32, "slow": 96, "volatility": 32}, build_exp2),
    "3": Experiment("Experiment 3", objective_exp3, {"fast": 32, "slow": 96, "vola": 32, "clip": 4.2}, build_exp3),
    "4": Experiment("Experiment 4", objective_exp4, {"fast": 32, "slow": 96, "vola": 32, "clip": 4.2}, build_exp4),
    "5": Experiment(
        "Experiment 5", objective_exp5, {"vola": 32, "clip": 4.2, "corr": 200, "shrinkage": 0.5}, build_exp5
    ),
}

# Exp 5 evaluates a per-row matrix solve (~3 s/trial); the rest are sub-second.
DEFAULT_TRIALS: dict[str, int] = {"1": 200, "2": 200, "3": 150, "4": 150, "5": 40}


def optimize(key: str, *, n_trials: int, seed: int) -> optuna.Study:
    """Run an Optuna study for a single experiment and print a summary."""
    experiment = EXPERIMENTS[key]
    baseline = experiment.default_sharpe()

    study = optuna.create_study(
        direction="maximize",
        study_name=experiment.name,
        sampler=optuna.samplers.TPESampler(seed=seed),
    )
    study.optimize(experiment.objective, n_trials=n_trials, show_progress_bar=False)

    print(f"\n{'═' * 60}")
    print(f"{experiment.name}  ({n_trials} trials)")
    print(f"{'─' * 60}")
    print(f"  baseline Sharpe (defaults {experiment.default_params}): {baseline:.4f}")
    print(f"  best Sharpe:     {study.best_value:.4f}")
    print(f"  best params:     {study.best_params}")
    improvement = study.best_value - baseline
    print(f"  improvement:     {improvement:+.4f} ({improvement / abs(baseline):+.1%})")
    print(f"{'═' * 60}")
    return study


def main(argv: list[str] | None = None) -> None:
    """Parse command-line arguments and run the requested Optuna study/studies."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--experiment",
        "-e",
        default="all",
        choices=[*EXPERIMENTS.keys(), "all"],
        help="Which experiment to optimize (1-5, or 'all'). Default: all.",
    )
    parser.add_argument(
        "--trials",
        "-n",
        type=int,
        default=None,
        help="Number of Optuna trials. Default: per-experiment (see DEFAULT_TRIALS).",
    )
    parser.add_argument("--seed", "-s", type=int, default=42, help="Sampler seed for reproducibility.")
    parser.add_argument("--verbose", action="store_true", help="Show Optuna's per-trial logging.")
    args = parser.parse_args(argv)

    if not args.verbose:
        optuna.logging.set_verbosity(optuna.logging.WARNING)

    keys = list(EXPERIMENTS.keys()) if args.experiment == "all" else [args.experiment]
    for key in keys:
        n_trials = args.trials if args.trials is not None else DEFAULT_TRIALS[key]
        optimize(key, n_trials=n_trials, seed=args.seed)


if __name__ == "__main__":
    main()
