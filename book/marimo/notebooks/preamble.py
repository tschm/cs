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

#: Price file every notebook reads, from the ``public/`` directory beside it.
PRICES_CSV = "Prices_hashed.csv"


def load_notebook(name: str) -> dict[str, Any]:
    """Execute sibling notebook ``name`` (e.g. ``"Experiment1.py"``) and return its namespace.

    The returned dict maps top-level names defined by the notebook to their
    values, so callers can pull out the signal function with
    ``load_notebook("Experiment1.py")["f"]``.

    Executing this module itself is the cheapest demonstration of that contract —
    the shared helpers come back as ordinary entries in the namespace:

        >>> namespace = load_notebook("preamble.py")
        >>> sorted(name for name in namespace if name in {"date_col", "load_prices"})
        ['date_col', 'load_prices']
    """
    return runpy.run_path(str(NOTEBOOK_DIR / name))


def load_prices(notebook_file: str) -> pl.DataFrame:
    """Load and preprocess prices from the standard CSV file.

    ``notebook_file`` is the *caller's* own path — the notebooks pass ``__file__`` —
    and the CSV is read from its ``public/`` sibling directory. The frame comes back
    with the date column first as nanosecond datetimes, every remaining column (one
    per asset) cast to ``Float64``, and gaps interpolated:

        >>> prices = load_prices(str(NOTEBOOK_DIR / "preamble.py"))
        >>> prices.columns[0]
        'date'
        >>> prices[date_col].dtype
        Datetime(time_unit='ns', time_zone=None)
        >>> set(prices.drop(date_col).dtypes) == {pl.Float64}
        True

    An absent CSV is checked for here rather than left to ``pl.read_csv``, so the
    error names the file that was looked for — the file ships with the repository,
    so its absence is a setup problem with an obvious remedy:

        >>> try:
        ...     load_prices(str(NOTEBOOK_DIR / "elsewhere" / "preamble.py"))
        ... except FileNotFoundError as error:
        ...     PRICES_CSV in str(error)
        True
    """
    path = Path(notebook_file).parent / "public" / PRICES_CSV
    if not path.is_file():
        msg = f"Price data not found: {path} — it ships with the repository; check the checkout is complete."
        raise FileNotFoundError(msg)
    dframe = pl.read_csv(str(path), try_parse_dates=True)
    dframe = dframe.with_columns(pl.col(date_col).cast(pl.Datetime("ns")))
    dframe = dframe.with_columns([pl.col(col).cast(pl.Float64) for col in dframe.columns if col != date_col])
    return interpolate(dframe)
