import calendar
from collections import OrderedDict

import numpy as np
import pandas as pd


def drawdown(series) -> pd.Series:
    """
    Compute the drawdown for a price series. The drawdown is defined as 1 - price/highwatermark.
    The highwatermark at time t is the highest price that has been achieved before or at time t.

    Args:
        series:

    Returns: Drawdown as a pandas series
    """
    return _Drawdown(series).drawdown


def monthlytable(nav) -> pd.DataFrame:
    """
    Get a table of monthly returns

    :param nav:

    :return:
    """
    def _cumulate(x):
        return (1 + x).prod() - 1.0

    r = nav.pct_change().dropna()
    # Works better in the first month
    # Compute all the intramonth-returns, instead of reapplying some monthly resampling of the NAV
    return_monthly = r.groupby([r.index.year, r.index.month]).apply(_cumulate)
    frame = return_monthly.unstack(level=1).rename(columns=lambda x: calendar.month_abbr[x])
    ytd = frame.apply(_cumulate, axis=1)
    frame["STDev"] = np.sqrt(12) * frame.std(axis=1)
    # make sure that you don't include the column for the STDev in your computation
    frame["YTD"] = ytd
    frame.index.name = "Year"
    frame.columns.name = None
    # most recent years on top
    return frame.iloc[::-1]


def performance(nav):
    return NavSeries(nav).summary()


class NavSeries(pd.Series):
    def __init__(self, *args, **kwargs):
        super(NavSeries, self).__init__(*args, **kwargs)
        if not self.empty:
            # check that all indices are increasing
            assert self.index.is_monotonic_increasing
            # make sure all entries non-negative
            assert not (self < 0).any(), "Problem with data:\n{x}".format(x=self.series)

    @property
    def series(self) -> pd.Series:
        return pd.Series({t: v for t, v in self.items()})

    @property
    def periods_per_year(self):
        if len(self.index) >= 2:
            x = pd.Series(data=self.index)
            return np.round(365 * 24 * 60 * 60 / x.diff().mean().total_seconds(), decimals=0)
        else:
            return 256

    def annualized_volatility(self, periods=None):
        t = periods or self.periods_per_year
        return np.sqrt(t) * self.dropna().pct_change().std()

    @staticmethod
    def __gmean(a):
        # geometric mean A
        # Prod [a_i] == A^n
        # Apply log on both sides
        # Sum [log a_i] = n log A
        # => A = exp(Sum [log a_i] // n)
        return np.exp(np.mean(np.log(a)))


    @property
    def returns(self) -> pd.Series:
        return self.pct_change().dropna()

    @property
    def __cum_return(self):
        return (1.0 + self.returns).prod() - 1.0

    def sharpe_ratio(self, periods=None, r_f=0):
        return (self.annual_r - r_f) / self.annualized_volatility(periods)

    @property
    def annual(self):
        return NavSeries(self.resample("A").last())

    @property
    def annual_r(self):
        r = NavSeries(self.resample("A").last()).pct_change()
        return self.__gmean(r + 1) - 1.0

    def summary(self, r_f=0):
        periods = self.periods_per_year

        d = OrderedDict()

        d["Return"] = 100 * self.__cum_return

        d["Annua Return"] = 100 * self.annual_r
        d["Annua Volatility"] = 100 * self.annualized_volatility(periods=periods)
        d["Annua Sharpe Ratio (r_f = {0})".format(r_f)] = self.sharpe_ratio(periods=periods, r_f=r_f)
        d["Max Drawdown"] = 100 * drawdown(self).max()
        d["Kurtosis"] = self.pct_change().kurtosis()

        x = pd.Series(d)
        x.index.name = "Performance number"

        return x


class _Drawdown(object):
    def __init__(self, series: pd.Series) -> object:
        """
        Drawdown for a given series
        :param series: pandas Series
        :param eps: a day is down day if the drawdown (positive) is larger than eps
        """
        # check series is indeed a series
        assert isinstance(series, pd.Series)
        # check that all indices are increasing
        assert series.index.is_monotonic_increasing
        # make sure all entries non-negative
        assert not (series < 0).any()

        self.__series = series

    @property
    def highwatermark(self) -> pd.Series:
        return self.__series.expanding(min_periods=1).max()

    @property
    def drawdown(self) -> pd.Series:
        return 1 - self.__series / self.highwatermark
