"""Shared pytest fixtures for experiment signal function tests.

Security Notes:
- S101 (assert usage): Asserts are used in pytest tests to validate conditions.
- Test code operates in a controlled environment with trusted inputs.
"""

import polars as pl
import pytest

N = 600  # satisfies min_samples=300 (the highest requirement across all experiments)


@pytest.fixture
def rising():
    """Return a DataFrame with a monotonically rising price series."""
    return pl.DataFrame({"p": [float(i) for i in range(1, N + 1)]})


@pytest.fixture
def falling():
    """Return a DataFrame with a monotonically falling price series."""
    return pl.DataFrame({"p": [float(i) for i in range(N, 0, -1)]})
