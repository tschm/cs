"""Shared pytest fixtures for experiment signal function tests.

Security Notes:
- S101 (assert usage): Asserts are used in pytest tests to validate conditions.
- Test code operates in a controlled environment with trusted inputs.
"""

import sys
from pathlib import Path

import polars as pl
import pytest

# Bootstrap the notebook directory onto sys.path once, here, so every test
# module can ``from preamble import load_notebook`` (the shared notebook loader)
# instead of repeating its own ``sys.path`` + ``runpy`` boilerplate. The
# notebooks are not an importable package, so this single insert is the price of
# reaching their shared ``preamble`` helper module.
NOTEBOOK_DIR = (Path(__file__).resolve().parents[1] / "book" / "marimo" / "notebooks").resolve()
if str(NOTEBOOK_DIR) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_DIR))

N = 600  # satisfies min_samples=300 (the highest requirement across all experiments)


@pytest.fixture
def rising():
    """Return a DataFrame with a monotonically rising price series."""
    return pl.DataFrame({"p": [float(i) for i in range(1, N + 1)]})


@pytest.fixture
def falling():
    """Return a DataFrame with a monotonically falling price series."""
    return pl.DataFrame({"p": [float(i) for i in range(N, 0, -1)]})
