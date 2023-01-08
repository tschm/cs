import pandas as pd

from .performance import monthlytable
from .performance import performance

from dataclasses import dataclass

@dataclass(frozen=True)
class Analysis:
    nav: pd.Series
    
    @property
    def monthlytable(self):
        m = 100*monthlytable(self.nav)
        m = m.applymap('{:,.2f}%'.format)
        m[m=="nan%"] = ""
        return m

    @property
    def performance(self):
        perf = performance(self.nav.resample("W").last())
        perf = perf.loc[["Annua Return", "Annua Volatility", "Annua Sharpe Ratio (r_f = 0)", "Max Drawdown", "Return", "Kurtosis"]]
        return perf.apply('{:,.2f}'.format)

    @property
    def std(self):
        return self.nav.pct_change().ewm(com=32).std().resample("W").last()
    