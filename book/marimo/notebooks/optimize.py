"""Optuna parameter optimization for the CTA experiments.

Each ``ExperimentN.py`` marimo notebook defines a signal function ``f(...)`` and
builds a :class:`jquantstats.Portfolio` whose Sharpe ratio its sliders tune by
hand. This module replays the same portfolio construction (reusing each notebook's
``f`` via :func:`runpy.run_path` and the TinyCTA API) and hands the search to
Optuna, maximizing the Sharpe over each experiment's parameter space. Strategy
logic thus lives once in the notebooks; only the search space lives here. Run it as
``python optimize.py --experiment {1..5|all} [--trials N]``.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from collections.abc import Callable
from functools import cache
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

# Data/signal accessors are ``@cache``d, so importing this module reads no CSV and
# runs no notebook. ``clip`` is a fixed winsorizing level, not a search dimension.
CLIP = 4.2


@cache
def _prices() -> pl.DataFrame:
    """Load the price frame once (date column plus one column per asset)."""
    return load_prices(str(NOTEBOOK_DIR / "optimize.py"))


@cache
def _prices_only() -> pl.DataFrame:
    """The price frame with the date column dropped."""
    return _prices().drop(date_col)


@cache
def _assets() -> list[str]:
    """Column names of the tradable assets (price columns, no date)."""
    return _prices_only().columns


@cache
def _notebook(name: str) -> dict[str, Any]:
    """Execute (and cache) a notebook's namespace (its ``f`` / ``dcc_correlation``)."""
    return load_notebook(name)


def _signal(notebook: str) -> Callable[..., Any]:
    """The signal function ``f`` defined by an experiment notebook."""
    return cast("Callable[..., Any]", _notebook(notebook)["f"])


def _sharpe(portfolio: Portfolio) -> float:
    """Return the portfolio's annualized Sharpe ratio (the optimization target)."""
    value = portfolio.stats.sharpe()["returns"]
    return float(value) if np.isfinite(value) else float("-inf")


# Portfolio builders — one per experiment, mirroring each notebook cell.
def build_exp1(*, fast: int, slow: int) -> Portfolio:
    """CTA 1.0 — sign of the fast-minus-slow EWM crossover."""
    f = _signal("Experiment1.py")
    signals = _prices_only().select(f(pl.all(), fast=fast, slow=slow).fill_null(0.0) * 5e6)
    return Portfolio.from_cash_position(prices=_prices(), cash_position=signals, aum=1e8)


def build_exp2(*, fast: int, slow: int, volatility: int) -> Portfolio:
    """CTA 2.0 — volatility-scaled crossover."""
    f = _signal("Experiment2.py")
    signals = _prices_only().select(f(pl.all(), fast=fast, slow=slow, volatility=volatility).fill_null(0.0) * 1e5)
    return Portfolio.from_cash_position(prices=_prices(), cash_position=signals, aum=1e8)


def build_exp3(*, fast: int, slow: int, vola: int, clip: float) -> Portfolio:
    """CTA 3.0 — tanh oscillator on vol-adjusted prices, divided by volatility."""
    f = _signal("Experiment3.py")
    signals = _prices_only().select(
        (f(pl.all(), fast=fast, slow=slow, vola=vola, clip=clip) * 1e5).fill_nan(0.0).fill_null(0.0)
    )
    return Portfolio.from_cash_position(prices=_prices(), cash_position=signals, aum=1e8)


def build_exp4(*, fast: int, slow: int, vola: int, clip: float) -> Portfolio:
    """CTA 4.0 — Euclidean risk-scaling across assets (optimization 1.0)."""
    prices_only = _prices_only()
    f = _signal("Experiment4.py")
    mu_np = prices_only.select(f(pl.all(), fast=fast, slow=slow, vola=vola, clip=clip)).to_numpy()
    volax_np = prices_only.select(pl.all().fill_nan(None).pct_change().ewm_std(com=vola, min_samples=vola)).to_numpy()
    euclid_norm = np.sqrt(np.nansum(mu_np**2, axis=1, keepdims=True))
    euclid_norm[euclid_norm == 0] = np.nan
    risk_scaled_np = mu_np / euclid_norm
    pos_np = np.nan_to_num(5e5 * risk_scaled_np / volax_np, nan=0.0)
    return _portfolio_from_matrix(pos_np)


def _day_position(matrix: np.ndarray, expected_mu: np.ndarray, expected_vo: np.ndarray) -> np.ndarray | None:
    """Risk-scaled position for one day, or ``None`` for a degenerate day (singular / zero norm)."""
    # inv_a_norm/solve resolve from module globals so tests can monkeypatch them.
    try:
        norm = inv_a_norm(expected_mu, matrix)
    except ValueError:
        # Singular correlation matrix on this day; skip the day, not the trial.
        return None
    if norm == 0 or np.isnan(norm):
        return None
    return cast("np.ndarray", np.nan_to_num(1e6 * (solve(matrix, expected_mu) / norm) / expected_vo, nan=0.0))


def _solve_positions(
    cor_3d: np.ndarray, mu: np.ndarray, vo: np.ndarray, prices_np: np.ndarray, *, shrinkage: float
) -> np.ndarray:
    """Per-day risk-parity positions from the shrunk DCC tensor; ill-conditioned days go flat."""
    n_rows, n_assets = prices_np.shape
    pos_matrix = np.zeros((n_rows, n_assets))
    # Silence the numerical noise from the ill-conditioned days the search explores
    # (matched by message to avoid importing cvx's internal warning classes).
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Matrix condition number")
        warnings.filterwarnings("ignore", category=RuntimeWarning, message="invalid value encountered in sqrt")
        for _n in range(n_rows):
            _mask = np.isfinite(prices_np[_n])
            if _mask.sum() == 0:
                continue
            _matrix = shrink2id(cor_3d[_n], lamb=shrinkage)[_mask, :][:, _mask]
            _pos = _day_position(_matrix, np.nan_to_num(mu[_n][_mask]), np.nan_to_num(vo[_n][_mask]))
            if _pos is not None:
                pos_matrix[_n, _mask] = _pos
    return pos_matrix


def build_exp5(*, vola: int, clip: float, corr: int, shrinkage: float) -> Portfolio:
    """CTA 5.0 — DCC correlation + shrinkage optimization; fast/slow fixed at 32/96 (optimization 2.0)."""
    prices_only = _prices_only()
    dcc_correlation = _notebook("Experiment5.py")["dcc_correlation"]
    cor_3d = dcc_correlation(prices_only, vola=vola, clip=clip, corr=corr)
    f = _signal("Experiment5.py")
    mu = prices_only.select(f(pl.all(), fast=32, slow=96, vola=vola, clip=clip)).to_numpy()
    vo = prices_only.select(pl.all().fill_nan(None).pct_change().ewm_std(com=vola, min_samples=int(vola))).to_numpy()
    pos_matrix = _solve_positions(cor_3d, mu, vo, prices_only.to_numpy(), shrinkage=shrinkage)
    return _portfolio_from_matrix(pos_matrix)


def _portfolio_from_matrix(pos_np: np.ndarray) -> Portfolio:
    """Wrap a (rows x assets) position matrix into a Portfolio with the date column."""
    prices = _prices()
    cash_position = pl.concat(
        [prices.select(date_col), pl.from_numpy(pos_np, schema=dict.fromkeys(_assets(), pl.Float64))],
        how="horizontal_extend",
    )
    return Portfolio.from_cash_position(prices=prices, cash_position=cash_position, aum=1e8)


# Optuna search spaces. Ranges mirror the marimo sliders (4..192 step 4); ``clip`` is
# fixed at ``CLIP``; ``slow`` is drawn strictly above ``fast`` so the oscillator holds.
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


# Experiment registry.
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
    if baseline == 0:
        # A zero baseline Sharpe has no meaningful percentage; report absolute only.
        print(f"  improvement:     {improvement:+.4f} (n/a — zero baseline)")
    else:
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
