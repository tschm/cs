import pandas as pd

def test_analysis(resource_dir):
    prices = pd.read_csv(resource_dir / "prices.csv", index_col=0, parse_dates=True, header=0)
    print(prices)
    assert False
