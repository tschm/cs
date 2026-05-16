"""Tests for the signal function f defined in Experiment 2."""

import runpy
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "book" / "marimo" / "notebooks"

f = runpy.run_path(str(NOTEBOOK_DIR / "Experiment2.py"))["f"]


def test_f_rising_trend_gives_positive_signal(rising):
    result = rising.select(f(pl.col("p")).drop_nulls())
    assert (result["p"] > 0).all()


def test_f_falling_trend_gives_negative_signal(falling):
    result = falling.select(f(pl.col("p")).drop_nulls())
    assert (result["p"] < 0).all()


def test_f_nulls_before_min_samples(rising):
    result = rising.select(f(pl.col("p")))
    assert result["p"].null_count() >= 299


def test_f_default_fast_is_32(rising):
    default = rising.select(f(pl.col("p")).drop_nulls())
    explicit = rising.select(f(pl.col("p"), fast=32).drop_nulls())
    assert default.equals(explicit)


def test_f_default_slow_is_96(rising):
    default = rising.select(f(pl.col("p")).drop_nulls())
    explicit = rising.select(f(pl.col("p"), slow=96).drop_nulls())
    assert default.equals(explicit)


def test_f_default_volatility_is_32(rising):
    default = rising.select(f(pl.col("p")).drop_nulls())
    explicit = rising.select(f(pl.col("p"), volatility=32).drop_nulls())
    assert default.equals(explicit)


def test_f_different_params_give_different_results():
    prices = pl.DataFrame({"p": [float(i) for i in range(1, 601)] + [float(i) for i in range(600, 0, -1)]})
    default_signal = prices.select(f(pl.col("p")).drop_nulls())
    fast_signal = prices.select(f(pl.col("p"), fast=4, slow=8).drop_nulls())
    assert not default_signal.equals(fast_signal)
