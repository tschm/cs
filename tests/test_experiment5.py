"""Tests for the signal function f defined in Experiment 5."""

import polars as pl
from preamble import load_notebook

f = load_notebook("Experiment5.py")["f"]


def test_f_signal_is_bounded_by_tanh(rising):
    """Signal is bounded to [-1, 1] via tanh."""
    result = rising.select(f(pl.col("p")).drop_nulls())
    assert (result["p"] >= -1).all()
    assert (result["p"] <= 1).all()


def test_f_rising_trend_gives_positive_signal(rising):
    """Rising price trend produces a non-negative signal."""
    result = rising.select(f(pl.col("p")).drop_nulls())
    assert (result["p"] >= 0).all()


def test_f_falling_trend_gives_negative_signal(falling):
    """Falling price trend produces a non-positive signal."""
    result = falling.select(f(pl.col("p")).drop_nulls())
    assert (result["p"] <= 0).all()


def test_f_nulls_before_min_samples(rising):
    """Signal is null for the first min_samples rows."""
    result = rising.select(f(pl.col("p")))
    assert result["p"].null_count() >= 299


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


def test_f_default_vola_is_32(rising):
    """Default vola parameter equals 32."""
    default = rising.select(f(pl.col("p")).drop_nulls())
    explicit = rising.select(f(pl.col("p"), vola=32).drop_nulls())
    assert default.equals(explicit)


def test_f_default_clip_is_4_2(rising):
    """Default clip parameter equals 4.2."""
    default = rising.select(f(pl.col("p")).drop_nulls())
    explicit = rising.select(f(pl.col("p"), clip=4.2).drop_nulls())
    assert default.equals(explicit)


def test_f_different_params_give_different_results():
    """Different fast/slow parameters produce different signal outputs."""
    prices = pl.DataFrame({"p": [float(i) for i in range(1, 601)] + [float(i) for i in range(600, 0, -1)]})
    default_signal = prices.select(f(pl.col("p")).drop_nulls())
    fast_signal = prices.select(f(pl.col("p"), fast=4, slow=8).drop_nulls())
    assert not default_signal.equals(fast_signal)
