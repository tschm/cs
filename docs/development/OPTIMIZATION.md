# Parameter optimization

The experiment notebooks expose their strategy parameters as marimo sliders so
you can tune the Sharpe ratio by hand. `book/marimo/notebooks/optimize.py`
automates that tuning with [Optuna](https://optuna.org): it replays each
notebook's exact portfolio construction and searches the parameter space for the
configuration that maximizes the portfolio Sharpe ratio.

## The notebooks-are-the-source-of-truth contract

The single most important rule in this module:

> **Strategy logic lives in the notebooks. Only the search space lives in
> `optimize.py`.**

Each `ExperimentN.py` notebook defines a signal function `f(...)`. `optimize.py`
does **not** re-implement those signals — it imports the live `f` from each
notebook and reuses it:

```python
from preamble import load_notebook

f = load_notebook("Experiment1.py")["f"]
```

`load_notebook` (in `book/marimo/notebooks/preamble.py`) is the one place that
executes a notebook via `runpy.run_path` and returns its namespace. The same
helper is used by the test suite, so notebooks, the optimizer, and the tests all
load strategy code through a single mechanism. This is what keeps the optimizer
from silently drifting away from the notebooks it is supposed to optimize.

The `build_exp*` functions in `optimize.py` mirror each notebook's portfolio
cell (signal → positions → `Portfolio.from_cash_position`). They are tied to the
notebooks numerically by the pinned Sharpe baselines in
`tests/expected_sharpe.py` — see [SHARPE_PINS.md](SHARPE_PINS.md). If a builder
stops reproducing its notebook's Sharpe ratio, the test suite fails.

## How the search is structured

| Piece | Role |
| --- | --- |
| `build_expN(...)` | Rebuilds experiment *N*'s portfolio for an explicit parameter set (mirrors the notebook cell). |
| `objective_expN(trial)` | Samples a trial's parameters and returns the resulting portfolio Sharpe ratio. |
| `_sharpe(portfolio)` | The optimization target: the annualized Sharpe ratio, mapped to `-inf` when non-finite so degenerate regions are discarded. |
| `Experiment` / `EXPERIMENTS` | Registry binding each objective to its notebook-default parameters (the baseline reported against). |
| `optimize(key, ...)` | Runs one Optuna study (TPE sampler, `direction="maximize"`) and prints baseline vs. best. |

### Search spaces

- `fast`, `slow`, `vola`, `volatility` mirror the marimo sliders: `4..192` in
  steps of `4`.
- `slow` is always drawn **strictly above** `fast` (`_suggest_fast_slow`) so the
  crossover keeps its fast/slow meaning and the oscillator stays well-defined.
- `clip` is held fixed at `4.2` (`CLIP`) rather than searched — it is a
  winsorizing level, not a strategy dimension.
- Experiment 5 additionally searches `corr` (`50..500`) and `shrinkage`
  (`0.0..1.0`), holding `fast`/`slow` at the notebook's fixed `32`/`96`.

`DEFAULT_TRIALS` sets a per-experiment trial budget — Experiment 5 evaluates a
per-row matrix solve (~3 s/trial) and so gets fewer trials than the sub-second
experiments.

## Running it

```bash
# Optimize one experiment
python book/marimo/notebooks/optimize.py --experiment 3 --trials 200

# Optimize all of them with the per-experiment default budgets
python book/marimo/notebooks/optimize.py --experiment all

# Reproducible runs and Optuna's per-trial logging
python book/marimo/notebooks/optimize.py -e 1 -n 50 --seed 7 --verbose
```

Each run prints the baseline Sharpe (notebook defaults), the best Sharpe found,
the winning parameters, and the improvement.

## Testing

`tests/test_optimize.py` covers the builders, the objectives, the search-space
bounds, and the CLI entry point. Coverage is measured with **branch** coverage
enabled (`[tool.coverage.run] branch = true` in `pyproject.toml`) at a 100%
threshold, so every guard and dispatch branch in `optimize.py` is exercised.
