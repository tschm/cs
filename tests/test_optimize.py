"""Tests for the Optuna parameter-optimization module (optimize.py)."""

import math
import runpy
import sys
from pathlib import Path

import optuna
import pytest
from expected_sharpe import (
    EXPECTED_SHARPE_RATIOS,
    SHARPE_RATIO_ABS_TOLERANCE,
    SHARPE_RATIO_REL_TOLERANCE,
)

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
    assert experiment.default_sharpe() == pytest.approx(optimize["_sharpe"](direct))


@pytest.mark.parametrize("key", sorted(optimize["EXPERIMENTS"]))
def test_builder_matches_pinned_notebook_sharpe(key):
    """Every builder run with notebook defaults reproduces the pinned notebook Sharpe.

    The build_exp* functions deliberately mirror each notebook's portfolio
    construction; this ties them to the notebooks numerically so the two
    cannot silently diverge.
    """
    experiment = optimize["EXPERIMENTS"][key]
    assert experiment.default_sharpe() == pytest.approx(
        EXPECTED_SHARPE_RATIOS[f"Experiment{key}"],
        rel=SHARPE_RATIO_REL_TOLERANCE,
        abs=SHARPE_RATIO_ABS_TOLERANCE,
    )


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


@pytest.mark.parametrize("key", ["3", "4", "5"])
def test_objective_returns_finite_value(key):
    """Each remaining experiment's Optuna objective evaluates to a finite Sharpe.

    Experiments 1 and 2 are covered by the fast/slow ordering test; this
    exercises the objective bodies for 3, 4 and 5 (and the builders behind
    them) with a minimal study.
    """
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=0))
    study.optimize(optimize["EXPERIMENTS"][key].objective, n_trials=1)
    assert math.isfinite(study.best_value)


def test_build_exp5_skips_singular_days(monkeypatch):
    """A singular daily correlation matrix is skipped rather than aborting the build."""

    def _raise(*_args, **_kwargs):
        """Stand in for inv_a_norm, mimicking TinyCTA's singular-matrix ValueError."""
        raise ValueError

    # build_exp5 resolves inv_a_norm from its own module globals (runpy returns a
    # copy of the namespace, so patch the function's __globals__ directly). Force
    # every day to hit the SingularMatrixError guard and confirm the build still
    # returns a Portfolio (all-zero positions) instead of aborting.
    build_exp5 = optimize["build_exp5"]
    monkeypatch.setitem(build_exp5.__globals__, "inv_a_norm", _raise)
    portfolio = build_exp5(vola=32, clip=4.2, corr=200, shrinkage=0.5)
    assert portfolio.stats.sharpe()["returns"] is not None


def test_main_runs_single_experiment(capsys):
    """The CLI entry point runs one experiment and prints its summary."""
    optimize["main"](["--experiment", "1", "--trials", "1"])
    out = capsys.readouterr().out
    assert "Experiment 1" in out
    assert "best Sharpe" in out
