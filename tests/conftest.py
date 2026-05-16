"""Shared pytest fixtures for experiment signal function tests."""

import polars as pl
import pytest

N = 600  # satisfies min_samples=300 (the highest requirement across all experiments)


@pytest.fixture
def rising():
    return pl.DataFrame({"p": [float(i) for i in range(1, N + 1)]})


@pytest.fixture
def falling():
    return pl.DataFrame({"p": [float(i) for i in range(N, 0, -1)]})
