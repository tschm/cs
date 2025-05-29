import marimo

__generated_with = "0.13.14"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # CTA 5.0 - Optimization 2.0
        """
    )
    return


@app.cell
def _():
    import warnings

    import time

    import pandas as pd
    import numpy as np

    from cvx.simulator import Builder
    from cvx.simulator import interpolate

    from tinycta.linalg import solve, inv_a_norm
    from tinycta.signal import returns_adjust, osc, shrink2id

    warnings.simplefilter(action="ignore", category=FutureWarning)
    return (
        Builder,
        interpolate,
        inv_a_norm,
        np,
        osc,
        pd,
        returns_adjust,
        shrink2id,
        solve,
        time,
    )


@app.cell
def _(interpolate, pd):
    # Load prices
    prices = pd.read_csv("data/Prices_hashed.csv", index_col=0, parse_dates=True)

    # interpolate the prices
    prices = prices.apply(interpolate)
    return (prices,)


@app.cell
def _():
    from ipywidgets import Label, HBox, VBox, IntSlider, FloatSlider

    fast = IntSlider(min=4, max=192, step=4, value=32)
    slow = IntSlider(min=4, max=192, step=4, value=96)
    vola = IntSlider(min=4, max=192, step=4, value=32)
    winsor = FloatSlider(min=1.0, max=6.0, step=0.1, value=4.2)
    corr = IntSlider(min=50, max=500, step=10, value=200)
    shrinkage = FloatSlider(min=0.0, max=1.0, step=0.05, value=0.5)
    left_box = VBox(
        [
            Label("Fast Moving Average"),
            Label("Slow Moving Average"),
            Label("Volatility"),
            Label("Winsorizing"),
            Label("Correlation"),
            Label("Shrinkage"),
        ]
    )

    right_box = VBox([fast, slow, vola, winsor, corr, shrinkage])
    HBox([left_box, right_box])
    return corr, shrinkage, vola, winsor


@app.cell
def _(
    Builder,
    corr,
    inv_a_norm,
    np,
    osc,
    prices,
    returns_adjust,
    shrink2id,
    shrinkage,
    solve,
    time,
    vola,
    winsor,
):
    T = time.time()
    correlation = corr.value

    returns_adj = prices.apply(returns_adjust, com=vola.value, clip=winsor.value)

    # DCC by Engle
    cor = returns_adj.ewm(com=correlation, min_periods=correlation).corr()

    mu = np.tanh(returns_adj.cumsum().apply(osc)).values
    vo = prices.pct_change().ewm(com=vola.value, min_periods=vola.value).std().values

    builder = Builder(prices=prices, initial_aum=1e8)

    for n, (t, state) in enumerate(builder):
        mask = state.mask
        matrix = shrink2id(cor.loc[t[-1]].values, lamb=shrinkage.value)[mask, :][
            :, mask
        ]
        expected_mu = np.nan_to_num(mu[n][mask])
        expected_vo = np.nan_to_num(vo[n][mask])
        risk_position = solve(matrix, expected_mu) / inv_a_norm(expected_mu, matrix)
        builder.cashposition = 1e6 * risk_position / expected_vo
        builder.aum = state.aum

    portfolio = builder.build()
    print(time.time() - T)
    return (portfolio,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # Conclusions
        * Dramatic relativ improvements observable despite using the same signals as in previous Experiment.
        * Main difference here is to take advantage of cross-correlations in the risk measurement.
        * Possible to add constraints on individual assets or groups of them.
        * Possible to reflect trading costs in objective with regularization terms (Ridge, Lars, Elastic Nets, ...)
        """
    )
    return


@app.cell
def _(portfolio):
    portfolio.snapshot()
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
