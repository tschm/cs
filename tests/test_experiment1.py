"""Tests for the signal function f defined in Experiment 1."""

import polars as pl
from preamble import load_notebook

f = load_notebook("Experiment1.py")["f"]


def test_f_signal_values_are_sign(rising):
    """Signal values are +/-1 or 0 (sign function output)."""
    result = rising.select(f(pl.col("p")).drop_nulls())
    assert result["p"].is_in([-1.0, 0.0, 1.0]).all()


def test_f_rising_trend_gives_positive_signal(rising):
    """Rising price trend produces a positive signal."""
    result = rising.select(f(pl.col("p")).drop_nulls())
    assert (result["p"] == 1.0).all()


def test_f_falling_trend_gives_negative_signal(falling):
    """Falling price trend produces a negative signal."""
    result = falling.select(f(pl.col("p")).drop_nulls())
    assert (result["p"] == -1.0).all()


def test_f_nulls_before_min_samples(rising):
    """Signal is null for the first min_samples rows."""
    result = rising.select(f(pl.col("p")))
    assert result["p"].null_count() >= 99


def test_f_default_fast_is_32(rising):
    """Default fast parameter equals 32."""
    default = rising.select(f(pl.col("p")).drop_nulls())
    explicit = rising.select(f(pl.col("p"), fast=32).drop_nulls())
    assert default.equals(explicit)


def test_f_default_slow_is_96(rising):
    """Default slow parameter equals 96."""
    default = rising.select(f(pl.col("p")).drop_nulls())
    explicit = rising.select(f(pl.col("p"), slow=96).drop_nulls())
    assert default.equals(explicit)


def test_f_different_params_give_different_results():
    """Different fast/slow parameters produce different signal outputs."""
    # Up then down: fast params detect the reversal sooner than slow params.
    prices = pl.DataFrame({"p": [float(i) for i in range(1, 301)] + [float(i) for i in range(300, 0, -1)]})
    slow_signal = prices.select(f(pl.col("p")).drop_nulls())
    fast_signal = prices.select(f(pl.col("p"), fast=4, slow=8).drop_nulls())
    assert not slow_signal.equals(fast_signal)
