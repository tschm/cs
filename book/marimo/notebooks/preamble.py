"""Shared data loading for marimo experiment notebooks."""

from pathlib import Path

import plotly.io as pio
import polars as pl
from jquantstats import interpolate

pio.renderers.default = "plotly_mimetype"

date_col = "date"


def load_prices(notebook_file: str) -> pl.DataFrame:
    """Load and preprocess prices from the standard CSV file."""
    path = Path(notebook_file).parent / "public" / "Prices_hashed.csv"
    dframe = pl.read_csv(str(path), try_parse_dates=True)
    dframe = dframe.with_columns(pl.col(date_col).cast(pl.Datetime("ns")))
    dframe = dframe.with_columns([pl.col(col).cast(pl.Float64) for col in dframe.columns if col != date_col])
    return interpolate(dframe)
