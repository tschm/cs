"""Tests for the preamble module shared by marimo experiment notebooks."""

import runpy
from pathlib import Path

import plotly.io as pio
import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "book" / "marimo" / "notebooks"
NOTEBOOK_FILE = str(NOTEBOOK_DIR / "Experiment1.py")

preamble = runpy.run_path(str(NOTEBOOK_DIR / "preamble.py"))
load_prices = preamble["load_prices"]
date_col = preamble["date_col"]


@pytest.fixture(scope="module")
def prices_df():
    return load_prices(NOTEBOOK_FILE)


def test_date_col_constant():
    assert date_col == "date"


def test_plotly_renderer_is_set():
    assert pio.renderers.default == "plotly_mimetype"


def test_load_prices_returns_dataframe(prices_df):
    assert isinstance(prices_df, pl.DataFrame)


def test_load_prices_not_empty(prices_df):
    assert prices_df.height > 0
    assert prices_df.width > 0


def test_load_prices_has_date_column(prices_df):
    assert date_col in prices_df.columns


def test_load_prices_date_column_dtype(prices_df):
    assert prices_df[date_col].dtype == pl.Datetime("ns")


def test_load_prices_non_date_columns_are_float64(prices_df):
    for col in prices_df.columns:
        if col != date_col:
            assert prices_df[col].dtype == pl.Float64, f"Column {col!r} is not Float64"


def test_load_prices_interpolation_applied(prices_df):
    from jquantstats import interpolate

    path = Path(NOTEBOOK_FILE).parent / "public" / "Prices_hashed.csv"
    raw = pl.read_csv(str(path), try_parse_dates=True)
    raw = raw.with_columns(pl.col(date_col).cast(pl.Datetime("ns")))
    raw = raw.with_columns([pl.col(col).cast(pl.Float64) for col in raw.columns if col != date_col])

    assert prices_df.equals(interpolate(raw))
