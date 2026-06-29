"""Shared data loading for marimo experiment notebooks.

This module also hosts :func:`load_notebook`, the single place that executes a
sibling notebook (or ``optimize.py``) via :func:`runpy.run_path` and returns its
namespace. The experiment notebooks are not an importable package, so both
``optimize.py`` and the test suite need to read symbols (the signal ``f``, the
``build_exp*`` builders, …) out of a freshly executed notebook namespace;
centralizing that here keeps the ``runpy`` call in one place.
"""

import runpy
from pathlib import Path
from typing import Any

import plotly.io as pio
import polars as pl
from jquantstats import interpolate

pio.renderers.default = "plotly_mimetype"

date_col = "date"

#: Directory holding the marimo notebooks (this file's own directory).
NOTEBOOK_DIR = Path(__file__).resolve().parent


def load_notebook(name: str) -> dict[str, Any]:
    """Execute sibling notebook ``name`` (e.g. ``"Experiment1.py"``) and return its namespace.

    The returned dict maps top-level names defined by the notebook to their
    values, so callers can pull out the signal function with
    ``load_notebook("Experiment1.py")["f"]``.
    """
    return runpy.run_path(str(NOTEBOOK_DIR / name))


def load_prices(notebook_file: str) -> pl.DataFrame:
    """Load and preprocess prices from the standard CSV file."""
    path = Path(notebook_file).parent / "public" / "Prices_hashed.csv"
    dframe = pl.read_csv(str(path), try_parse_dates=True)
    dframe = dframe.with_columns(pl.col(date_col).cast(pl.Datetime("ns")))
    dframe = dframe.with_columns([pl.col(col).cast(pl.Float64) for col in dframe.columns if col != date_col])
    return interpolate(dframe)
