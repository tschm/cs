"""Tests for book/marimo/notebooks/preamble.py."""

import importlib.util
from pathlib import Path

import plotly.io as pio
import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "book" / "marimo" / "notebooks"


def _load_preamble():
    spec = importlib.util.spec_from_file_location("preamble", NOTEBOOK_DIR / "preamble.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


preamble = _load_preamble()


def test_date_col():
    assert preamble.date_col == "date"


def test_plotly_renderer():
    assert pio.renderers.default == "plotly_mimetype"


@pytest.fixture(scope="module")
def prices():
    return preamble.load_prices(str(NOTEBOOK_DIR / "Experiment1.py"))


def test_load_prices_returns_dataframe(prices):
    assert isinstance(prices, pl.DataFrame)


def test_load_prices_non_empty(prices):
    assert len(prices) > 0


def test_load_prices_has_date_column(prices):
    assert preamble.date_col in prices.columns
    assert prices[preamble.date_col].dtype == pl.Datetime("ns")


def test_load_prices_date_has_no_nulls(prices):
    assert prices[preamble.date_col].null_count() == 0


def test_load_prices_asset_columns_are_float64(prices):
    for col in prices.columns:
        if col != preamble.date_col:
            assert prices[col].dtype == pl.Float64
