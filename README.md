# 📈 [The 10-line CTA](http://tschm.github.io/cs)

[![pages-build-deployment](https://github.com/tschm/cs/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/tschm/cs/actions/workflows/pages/pages-build-deployment)
[![CodeFactor](https://www.codefactor.io/repository/github/tschm/cs/badge)](https://www.codefactor.io/repository/github/tschm/cs)
[![Renovate enabled](https://img.shields.io/badge/renovate-enabled-brightgreen.svg)](https://github.com/renovatebot/renovate)

## 🚀 About

Challenged by a young CEO, I wrote a terse CTA (Commodity Trading Advisor) investment
strategy in just 10 lines of code. This project discusses the somewhat quirky background
of this code fragment and explores how Convex Programming
opens the door to deeper insights into the strategy.

## ✨ Features

- 💰 Implement a hedge fund strategy in just 10 lines of code
- 📊 Boost the Sharpe Ratio through optimization techniques
- 📉 Control both Kurtosis and trading costs

## 🛠️ Getting Started

### 📋 Prerequisites

- Python 3.11+
- A POSIX shell. macOS and Linux have one by default.

> **🪟 Windows users:** The `make` targets are written for a POSIX shell and
> rely on tools like `mkdir -p`, `printf`, `curl`, and `[ … ]`. They will **not**
> run under `cmd.exe` or PowerShell — you'll see errors such as
> `process_begin: CreateProcess(NULL, # Ensure the … folder exists, …) failed.`
> Run the commands below from **WSL** (recommended) or **Git Bash**, both of
> which provide a POSIX shell.

### 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/tschm/cs.git
cd cs

# Install dependencies
make install
```

### 📖 Documentation

```bash
# Build the Jupyter Book
make book
```

Developer notes live under [`docs/development/`](docs/development/):

- [Parameter optimization](docs/development/OPTIMIZATION.md) — how the Optuna
  search in `optimize.py` reuses the notebook signals (the
  notebooks-are-the-source-of-truth contract).
- [Sharpe-ratio pins](docs/development/SHARPE_PINS.md) — the pinned regression
  baselines and how to update them.
- [Test-layout parity](docs/development/TEST_LAYOUT.md) — why tests mirror the
  notebooks (not a `src/` tree) and the repo-local gate that enforces it.

### 🔬 Running the Experiments

Each `ExperimentN.py` notebook is a self-contained CTA strategy. To search its
parameter space for the configuration that maximizes the portfolio Sharpe ratio,
run the Optuna driver in `book/marimo/notebooks/optimize.py`:

```bash
# Optimize a single experiment (1–5) with an explicit trial budget
python book/marimo/notebooks/optimize.py --experiment 3 --trials 200

# Optimize all five, each with its per-experiment default budget
python book/marimo/notebooks/optimize.py --experiment all

# Reproducible run with Optuna's per-trial logging (short flags)
python book/marimo/notebooks/optimize.py -e 1 -n 50 --seed 7 --verbose
```

Each run prints the baseline Sharpe (notebook defaults), the best Sharpe found,
the winning parameters, and the improvement. The driver never re-implements a
strategy — it imports each notebook's live signal function, so the notebooks stay
the single source of truth. See
[OPTIMIZATION.md](docs/development/OPTIMIZATION.md) for the full contract.

#### Regenerating the Sharpe baselines

The headline Sharpe of every experiment is pinned in
[`tests/expected_sharpe.py`](tests/expected_sharpe.py) and checked to a tight
`1e-6` tolerance by both the notebook and optimizer regression tests. A
dependency bump that legitimately shifts the numbers will fail those tests; the
assertion message prints the expected pin next to the freshly computed value:

```bash
# See old vs. new values for every experiment
uv run pytest tests/test_notebook_sharpe.py tests/test_optimize.py -v
```

Eyeball the deltas, and only if they are acceptable copy the new values into
`EXPECTED_SHARPE_RATIOS`, then re-run the suite so both test modules agree. The
full review checklist (and when *not* to re-pin) is in
[SHARPE_PINS.md](docs/development/SHARPE_PINS.md).

### 🧪 Interactive Development

```bash
# Start Marimo
make marimo
```

## ⚠️ DISCLAIMER

We do not guarantee or take responsibility for the accuracy, completeness,
reliability and usefulness of any information.

Dr. Thomas Schmelzer created all material in his personal capacity.
The views stated are his own and do not necessarily represent
the views of neither ADIA nor Stanford University. The opinion expressed
is based on the prevailing market trends and is subject to change.

## 🔗 Infrastructure

This project relies on the [Rhiza](https://jebel-quant.github.io/rhiza-education/) system
for its underlying infrastructure and tooling.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
