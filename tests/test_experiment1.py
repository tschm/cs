"""Tests for the signal function f defined in Experiment 1."""

import runpy
from pathlib import Path

import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "book" / "marimo" / "notebooks"

f = runpy.run_path(str(NOTEBOOK_DIR / "Experiment1.py"))["f"]

N = 200  # enough rows to satisfy min_samples=100


@pytest.fixture
def rising():
    return pl.DataFrame({"p": [float(i) for i in range(1, N + 1)]})


@pytest.fixture
def falling():
    return pl.DataFrame({"p": [float(i) for i in range(N, 0, -1)]})


def test_f_signal_values_are_sign(rising):
    result = rising.select(f(pl.col("p")).drop_nulls())
    assert result["p"].is_in([-1.0, 0.0, 1.0]).all()


def test_f_rising_trend_gives_positive_signal(rising):
    result = rising.select(f(pl.col("p")).drop_nulls())
    assert (result["p"] == 1.0).all()


def test_f_falling_trend_gives_negative_signal(falling):
    result = falling.select(f(pl.col("p")).drop_nulls())
    assert (result["p"] == -1.0).all()


def test_f_nulls_before_min_samples(rising):
    result = rising.select(f(pl.col("p")))
    assert result["p"].null_count() >= 99


def test_f_default_fast_is_32(rising):
    default = rising.select(f(pl.col("p")).drop_nulls())
    explicit = rising.select(f(pl.col("p"), fast=32).drop_nulls())
    assert default.equals(explicit)


def test_f_default_slow_is_96(rising):
    default = rising.select(f(pl.col("p")).drop_nulls())
    explicit = rising.select(f(pl.col("p"), slow=96).drop_nulls())
    assert default.equals(explicit)


def test_f_different_params_give_different_results():
    # Up then down: fast params detect the reversal sooner than slow params.
    prices = pl.DataFrame({"p": [float(i) for i in range(1, 301)] + [float(i) for i in range(300, 0, -1)]})
    slow_signal = prices.select(f(pl.col("p")).drop_nulls())
    fast_signal = prices.select(f(pl.col("p"), fast=4, slow=8).drop_nulls())
    assert not slow_signal.equals(fast_signal)
