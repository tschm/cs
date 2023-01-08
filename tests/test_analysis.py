import pytest
import pandas as pd
from pycta.analysis import Analysis

@pytest.fixture
def analysis(resource_dir):
    prices = pd.read_csv(resource_dir / "test_prices.csv", index_col=0, parse_dates=True, header=0)
    # we need only one time series
    nav = prices["B"]
    return Analysis(nav)


def test_std(analysis):
    assert analysis.std["2013-02-03"] == pytest.approx(0.004341629905864831)


def test_monthlytable(analysis):
    assert analysis.monthlytable["STDev"].loc[2015] == "18.89%"

    