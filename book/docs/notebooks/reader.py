import pandas as pd

if __name__ == '__main__':
    prices = pd.read_csv("data/futures_prices.csv", index_col=0, parse_dates=True, header=0)
    print(prices)