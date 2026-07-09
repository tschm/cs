"""Tests for the Optuna parameter-optimization module (optimize.py)."""

import math

import numpy as np
import optuna
import pytest
from expected_sharpe import (
    EXPECTED_SHARPE_RATIOS,
    SHARPE_RATIO_ABS_TOLERANCE,
    SHARPE_RATIO_REL_TOLERANCE,
)
from preamble import load_notebook

optimize = load_notebook("optimize.py")

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


def test_default_trials_cover_every_experiment():
    """DEFAULT_TRIALS has an entry for each registered experiment (no KeyError in main)."""
    assert set(optimize["DEFAULT_TRIALS"]) == set(optimize["EXPERIMENTS"])


def test_sharpe_returns_neg_inf_for_nonfinite_portfolio():
    """A degenerate (all-zero) portfolio has a non-finite Sharpe, mapped to -inf.

    Exercises the ``else float('-inf')`` branch of ``_sharpe`` that the search
    relies on to discard parameter regions that produce no usable returns.
    """
    zeros = np.zeros((len(optimize["_prices_only"]()), len(optimize["_assets"]())))
    portfolio = optimize["_portfolio_from_matrix"](zeros)
    assert optimize["_sharpe"](portfolio) == float("-inf")


def test_suggest_fast_slow_stays_within_slider_bounds():
    """Sampled (fast, slow) pairs honor the slider ranges and the fast < slow rule.

    Checks the boundaries of the shared ``_suggest_fast_slow`` search space:
    fast in [4, 96], slow in [fast+4, 192], both multiples of 4.
    """
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=1))
    study.optimize(optimize["objective_exp1"], n_trials=15)
    for trial in study.trials:
        fast, slow = trial.params["fast"], trial.params["slow"]
        assert 4 <= fast <= 96
        assert fast % 4 == 0
        assert fast + 4 <= slow <= 192
        assert slow % 4 == 0


def test_objective_exp5_samples_within_search_space():
    """Experiment 5's objective samples vola/corr/shrinkage within their declared ranges."""
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=2))
    study.optimize(optimize["objective_exp5"], n_trials=2)
    for trial in study.trials:
        assert 4 <= trial.params["vola"] <= 192
        assert 50 <= trial.params["corr"] <= 500
        assert 0.0 <= trial.params["shrinkage"] <= 1.0


def test_main_experiment_all_uses_default_trials_for_every_experiment(capsys, monkeypatch):
    """``--experiment all`` (no ``--trials``) dispatches to all experiments using DEFAULT_TRIALS.

    Exercises both the ``"all"`` key expansion and the
    ``n_trials = ... else DEFAULT_TRIALS[key]`` fallback branch in ``main``.
    DEFAULT_TRIALS is shrunk to a single trial each to keep the test fast.
    """
    for key in optimize["EXPERIMENTS"]:
        monkeypatch.setitem(optimize["DEFAULT_TRIALS"], key, 1)
    optimize["main"](["--experiment", "all"])
    out = capsys.readouterr().out
    for experiment in optimize["EXPERIMENTS"].values():
        assert experiment.name in out


def test_optimize_handles_zero_baseline(capsys, monkeypatch):
    """A zero baseline Sharpe prints 'n/a' instead of raising ZeroDivisionError.

    ``optimize`` divides the improvement by the baseline to report a percentage;
    forcing every Sharpe evaluation to 0 drives the baseline to exactly 0 and
    exercises the zero-baseline guard. Patch ``_sharpe`` in the module globals
    (the objective and ``Experiment.default_sharpe`` both resolve it there).
    """
    monkeypatch.setitem(optimize["optimize"].__globals__, "_sharpe", lambda _portfolio: 0.0)
    study = optimize["optimize"]("1", n_trials=1, seed=0)
    assert study.best_value == 0.0
    assert "n/a — zero baseline" in capsys.readouterr().out


def test_main_verbose_enables_optuna_logging(capsys, monkeypatch):
    """The ``--verbose`` flag leaves Optuna's per-trial logging enabled (skips the silencing branch)."""
    calls = []
    monkeypatch.setattr(optuna.logging, "set_verbosity", lambda level: calls.append(level))
    optimize["main"](["--experiment", "1", "--trials", "1", "--verbose"])
    # With --verbose, main must not silence Optuna by lowering verbosity to WARNING.
    assert optuna.logging.WARNING not in calls
