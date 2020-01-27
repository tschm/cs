import pandas as pd
from .performance import NavSeries


class Portfolio(object):
    def __init__(self, prices, position=None):
        if position is None:
            position = pd.DataFrame(index=prices.index, columns=prices.keys())

        assert prices.index.equals(position.index)
        assert set(prices.keys()) == set(position.keys())

        # avoid duplicates
        assert not prices.index.has_duplicates, "Price Index has duplicates"
        assert not position.index.has_duplicates, "Position Index has duplicates"

        assert prices.index.is_monotonic_increasing, "Price Index is not increasing"
        assert position.index.is_monotonic_increasing, "Position Index is not increasing"

        self.__prices = prices
        self.__position = position

    @property
    def prices(self):
        return self.__prices

    @property
    def position(self):
        return self.__position

    @property
    def profit(self):
        return (self.prices.pct_change() * self.position.shift(periods=1)).sum(axis=1)

    def nav(self, init_capital=None):
        # common problem for most CTAs.
        init_capital = init_capital or 100*self.profit.std()
        # We assume we start every day with the same initial capital!
        r = self.profit / init_capital
        # We then simply compound the nav!
        # We could also achieve the same by scaling the positions with increasing fundsize...
        return NavSeries((1+r).cumprod())

    def __setattr__(self, key, value):
        self.__position.loc[key] = value
