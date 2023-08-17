"""global fixtures"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture(scope="session", name="resource_dir")
def resource_fixture():
    """resource fixture"""
    return Path(__file__).parent / "resources"


@pytest.fixture
def prices(resource_dir):
    """prices fixture"""

    frame = pd.read_csv(
        resource_dir / "prices.csv", index_col=0, header=0, parse_dates=True
    )

    if not frame.index.is_monotonic_increasing:
        raise AssertionError

    return frame
