"""Tests for the Optuna parameter-optimization module (optimize.py)."""

import math
import runpy
import sys
from pathlib import Path

import optuna
import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "book" / "marimo" / "notebooks"
sys.path.insert(0, str(NOTEBOOK_DIR))

optimize = runpy.run_path(str(NOTEBOOK_DIR / "optimize.py"))

# Keep Optuna quiet during the test run.
optuna.logging.set_verbosity(optuna.logging.WARNING)


def test_build_exp1_returns_finite_sharpe():
    """A portfolio built with explicit parameters yields a finite Sharpe ratio."""
    portfolio = optimize["build_exp1"](fast=32, slow=96)
    sharpe = portfolio.stats.sharpe()["returns"]
    assert math.isfinite(sharpe)


def test_default_sharpe_matches_baseline_builder():
    """Experiment.default_sharpe reproduces the notebook defaults exactly."""
    experiment = optimize["EXPERIMENTS"]["1"]
    direct = optimize["build_exp1"](**experiment.default_params)
    assert experiment.default_sharpe() == optimize["_sharpe"](direct)


@pytest.mark.parametrize("key", ["1", "2"])
def test_objective_respects_fast_less_than_slow(key):
    """The search space never proposes fast >= slow for the crossover experiments."""
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=0))
    study.optimize(optimize["EXPERIMENTS"][key].objective, n_trials=5)
    for trial in study.trials:
        assert trial.params["fast"] < trial.params["slow"]


def test_optimize_finds_finite_best_value():
    """A short study on the cheapest experiment returns a finite, non-degenerate optimum."""
    study = optimize["optimize"]("1", n_trials=5, seed=42)
    assert math.isfinite(study.best_value)
    # With trend logic the best configuration should be a real positive Sharpe.
    assert study.best_value > 0
