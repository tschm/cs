from beakerx import *
from .performance import drawdown
from .performance import monthlytable
from .performance import performance


class Analysis(object):
    def __init__(self, nav):
        assert isinstance(nav, pd.DataFrame)
        self.__nav = nav

    @property
    def nav(self):
        return self.__nav

    @property
    def monthlytable(self):
        return 100 * monthlytable(self.__nav)

    @property
    def performance(self):
        #assert isinstance(nav, pd.DataFrame)
        perf = self.apply(performance)
        perf = perf.loc[["Annua Return", "Annua Volatility", "Annua Sharpe Ratio (r_f = 0)", "Max Drawdown", "Return", "Kurtosis"]]
        perf = perf.applymap(lambda x: float(x))
        #display = TableDisplay(perf)
        #dbl_format = TableDisplayStringFormat.getDecimalFormat(0, 2)
        #display.setStringFormatForType(ColumnType.Double, dbl_format)
        return perf


def __container():
    l = TabbedOutputContainerLayoutManager()
    l.setBorderDisplayed(False)
    o = OutputContainer()
    o.setLayoutManager(l)
    return o


def __display_monthtable(nav):
    display = TableDisplay(100 * monthlytable(nav))
    dbl_format = TableDisplayStringFormat.getDecimalFormat(2, 2)

    for column in display.chart.columnNames:
        display.setStringFormatForColumn(column, dbl_format)
        __filterColumn(display, column)

    return display


def __filterColumn(display, column, fct=lambda x: np.isnan(float(x)), update=""):
    # get the column index of the column
    col_index = display.chart.columnNames.index(column)

    # loop over all rows
    for row in range(len(display.values)):
        # if the entry is a NaN?
        if fct(display.values[row][col_index]):
            # update the cell
            display.updateCell(row, column, update)

    # send to the model
    display.sendModel()
    return display


def __nav_curve(nav, name=None, showLegend=True):
    p = TimePlot(xLabel="Time", yLabel="NAV", title=name, showLegend=showLegend, logY=True)

    y_axis = YAxis(label="Drawdown", upperMargin=2)
    p.add(y_axis)

    p.add(Line(nav.resample("W").last(), displayName="NAV"))
    p.add(Area(drawdown(nav.resample("W").last()), displayName="Drawdown", yAxis="Drawdown"))

    return p


def __std_curve(nav, com=32, name=None, showLegend=False):
    p = TimePlot(xLabel="Time", yLabel="StDev", title=name, showLegend=showLegend)
    p.add(Line(nav.pct_change().ewm(com=com).std().resample("W").last(), displayName=name))
    return p


def __display_performance(nav):
    assert isinstance(nav, pd.DataFrame)
    perf = nav.apply(performance)
    perf = perf.loc[["Annua Return", "Annua Volatility", "Annua Sharpe Ratio (r_f = 0)", "Max Drawdown", "Return", "Kurtosis"]]
    perf = perf.applymap(lambda x: float(x))
    display = TableDisplay(perf)
    dbl_format = TableDisplayStringFormat.getDecimalFormat(0, 2)
    display.setStringFormatForType(ColumnType.Double, dbl_format)
    return display


def analysis(nav, com=32, name=None):
    o = __container()
    o.addItem(__display_performance(nav.to_frame(name="NAV")), "Performance")
    o.addItem(__display_monthtable(nav), "Month/Year")
    o.addItem(__nav_curve(nav, name=name, showLegend=False), "NAV Curve")
    o.addItem(__std_curve(nav, com=com, name=name), "Moving Standard deviation")

    return o
