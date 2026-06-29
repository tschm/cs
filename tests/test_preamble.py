"""Tests for the preamble module shared by marimo experiment notebooks."""

from pathlib import Path

import plotly.io as pio
import polars as pl
import pytest
from preamble import NOTEBOOK_DIR, load_notebook

NOTEBOOK_FILE = str(NOTEBOOK_DIR / "Experiment1.py")

preamble = load_notebook("preamble.py")
load_prices = preamble["load_prices"]
date_col = preamble["date_col"]


@pytest.fixture(scope="module")
def prices_df():
    """Load prices from the Experiment1 notebook file."""
    return load_prices(NOTEBOOK_FILE)


def test_date_col_constant():
    """date_col constant equals 'date'."""
    assert date_col == "date"


def test_plotly_renderer_is_set():
    """Plotly renderer is set to 'plotly_mimetype' for notebook compatibility."""
    assert pio.renderers.default == "plotly_mimetype"


def test_load_prices_returns_dataframe(prices_df):
    """load_prices returns a polars DataFrame."""
    assert isinstance(prices_df, pl.DataFrame)


def test_load_prices_not_empty(prices_df):
    """Loaded DataFrame has at least one row and one column."""
    assert prices_df.height > 0
    assert prices_df.width > 0


def test_load_prices_has_date_column(prices_df):
    """Loaded DataFrame contains the date column."""
    assert date_col in prices_df.columns


def test_load_prices_date_column_dtype(prices_df):
    """Date column has Datetime(ns) dtype."""
    assert prices_df[date_col].dtype == pl.Datetime("ns")


def test_load_prices_non_date_columns_are_float64(prices_df):
    """All non-date columns are Float64."""
    for col in prices_df.columns:
        if col != date_col:
            assert prices_df[col].dtype == pl.Float64, f"Column {col!r} is not Float64"


def test_load_prices_interpolation_applied(prices_df):
    """load_prices applies interpolation to the raw data."""
    from jquantstats import interpolate

    path = Path(NOTEBOOK_FILE).parent / "public" / "Prices_hashed.csv"
    raw = pl.read_csv(str(path), try_parse_dates=True)
    raw = raw.with_columns(pl.col(date_col).cast(pl.Datetime("ns")))
    raw = raw.with_columns([pl.col(col).cast(pl.Float64) for col in raw.columns if col != date_col])

    assert prices_df.equals(interpolate(raw))
