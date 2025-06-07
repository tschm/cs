import marimo

__generated_with = "0.13.15"
app = marimo.App()

with app.setup:
    import numpy as np
    import pandas as pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# CTA 5.0 - Optimization 2.0""")
    return


@app.cell
def _():
    import warnings

    # Suppress noisy warnings
    warnings.simplefilter(action="ignore", category=FutureWarning)
    return


@app.cell
def _():
    import marimo as mo
    import plotly.io as pio

    # Ensure Plotly works with Marimo
    pio.renderers.default = "plotly_mimetype"
    return (mo,)


@app.cell
def _():
    from tinycta.linalg import inv_a_norm, solve
    from tinycta.signal import osc, returns_adjust, shrink2id

    return inv_a_norm, osc, returns_adjust, shrink2id, solve


@app.cell
def _(mo):
    # Load prices
    from cvx.simulator import interpolate

    prices = pd.read_csv(
        mo.notebook_location() / "public" / "Prices_hashed.csv",
        index_col=0,
        parse_dates=True,
    )

    # interpolate the prices
    prices = prices.apply(interpolate)
    return (prices,)


@app.cell
def _(mo):
    # Create sliders using marimo's UI components
    fast = mo.ui.slider(4, 192, step=4, value=32, label="Fast Moving Average")
    slow = mo.ui.slider(4, 192, step=4, value=96, label="Slow Moving Average")
    vola = mo.ui.slider(4, 192, step=4, value=32, label="Volatility")
    winsor = mo.ui.slider(1.0, 6.0, step=0.1, value=4.2, label="Winsorizing")
    corr = mo.ui.slider(50, 500, step=10, value=200, label="Correlation")
    shrinkage = mo.ui.slider(0.0, 1.0, step=0.05, value=0.5, label="Shrinkage")

    # Display the sliders in a vertical stack
    mo.vstack([fast, slow, vola, winsor, corr, shrinkage])

    return corr, shrinkage, vola, winsor


@app.cell
def _(
    corr,
    inv_a_norm,
    osc,
    prices,
    returns_adjust,
    shrink2id,
    shrinkage,
    solve,
    vola,
    winsor,
):
    from cvx.simulator import Builder

    correlation = corr.value

    returns_adj = prices.apply(returns_adjust, com=vola.value, clip=winsor.value)

    # DCC by Engle
    cor = returns_adj.ewm(com=correlation, min_periods=correlation).corr()

    mu = np.tanh(returns_adj.cumsum().apply(osc)).values
    vo = prices.pct_change().ewm(com=vola.value, min_periods=vola.value).std().values

    builder = Builder(prices=prices, initial_aum=1e8)

    for n, (t, state) in enumerate(builder):
        mask = state.mask
        matrix = shrink2id(cor.loc[t[-1]].values, lamb=shrinkage.value)[mask, :][:, mask]
        expected_mu = np.nan_to_num(mu[n][mask])
        expected_vo = np.nan_to_num(vo[n][mask])
        risk_position = solve(matrix, expected_mu) / inv_a_norm(expected_mu, matrix)
        builder.cashposition = 1e6 * risk_position / expected_vo
        builder.aum = state.aum

    portfolio = builder.build()
    print(portfolio.sharpe())
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


if __name__ == "__main__":
    app.run()
