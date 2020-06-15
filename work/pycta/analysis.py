import pandas as pd

from .performance import monthlytable
from .performance import performance


class Analysis(object):
    def __init__(self, nav):
        self.__nav = nav

    @property
    def monthlytable(self):
        m = 100*monthlytable(self.__nav)
        m = m.applymap('{:,.2f}%'.format)
        m[m=="nan%"] = ""
        return m

    @property
    def performance(self):
        perf = performance(self.__nav)
        perf = perf.loc[["Annua Return", "Annua Volatility", "Annua Sharpe Ratio (r_f = 0)", "Max Drawdown", "Return", "Kurtosis"]]
        return perf.apply('{:,.2f}'.format)

    @property
    def std(self):
        s = self.__nav.pct_change().ewm(com=32).std().resample("W").last()
        return pd.DataFrame(data=s, columns=["Moving Std"])

    @property
    def nav(self):
        b = self.__nav.resample("W").last()
        #d = 100*drawdown(b)
        return pd.DataFrame({"NAV": b})
