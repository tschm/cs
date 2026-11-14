# 📈 [The 10-line CTA](http://tschm.github.io/cs)

[![Book](https://github.com/tschm/cs/actions/workflows/rhiza_book.yml/badge.svg)](https://github.com/tschm/cs/actions/workflows/rhiza_book.yml)
[![CodeFactor](https://www.codefactor.io/repository/github/tschm/cs/badge)](https://www.codefactor.io/repository/github/tschm/cs)
[![Coverage](https://tschm.github.io/cs/coverage-badge.svg)](https://tschm.github.io/cs/reports/html-coverage/)
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
- [uv](https://docs.astral.sh/uv/) — `make` installs it into `./bin` if it is missing.
- A POSIX shell. macOS and Linux have one by default.

> **🪟 Windows users:** The `Makefile` is a thin shim that hands every target to
> [`rhiza-task`](https://jebel-quant.github.io/rhiza-education/), but the shim
> itself needs a POSIX shell (`command -v`, and `curl` to bootstrap uv). Run the
> commands below from **WSL** (recommended) or **Git Bash**, or call the task
> runner directly: `uvx rhiza-task@1.7.0 run <target>`.

### 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/tschm/cs.git
cd cs

# Install dependencies
make install
```

### 🗂️ Project Layout

```text
book/marimo/
├── notebooks/            # marimo notebooks only — Experiment1.py … Experiment5.py
│   └── public/           # the price data the notebooks read
└── helpers/              # plain Python modules shared by notebooks and tests
    ├── preamble.py       # price loading, load_notebook() / load_script()
    └── optimize.py       # Optuna driver for the experiments
docs/                     # site sources: index.md, development notes, paper
tests/                    # one test_<name>.py per notebook or helper module
```

There is no `src/` package. The notebooks are the source, and the two helper
modules sit next to them rather than inside `notebooks/`: the book build exports
every `*.py` in that folder with `marimo export`, which fails on a file that is
not a marimo notebook.

### 📖 Documentation

The companion site is built with [zensical](https://zensical.org) from
[`mkdocs.yml`](mkdocs.yml) and the [`docs/`](docs/) tree (this README is its home
page). `make book` first runs the test suite and compiles the paper, then exports
each experiment notebook to HTML, so the site carries the test and coverage
reports, the paper PDF and a **Notebooks** section with all five experiments.

```bash
# Build the companion site into _book/
make book

# Build it and serve it locally on http://localhost:8000
make serve

# Check that every nav entry resolves in the built site
make book-nav
```

Developer notes live under [`docs/development/`](docs/development/):

- [Parameter optimization](docs/development/OPTIMIZATION.md) — how the Optuna
  search in `optimize.py` reuses the notebook signals (the
  notebooks-are-the-source-of-truth contract).
- [Sharpe-ratio pins](docs/development/SHARPE_PINS.md) — the pinned regression
  baselines and how to update them.
- [Test-layout parity](docs/development/TEST_LAYOUT.md) — why tests mirror the
  notebooks and helper modules (not a `src/` tree) and the repo-local gate that
  enforces it.
- [Releasing](docs/development/RELEASING.md) — how a release is cut, and why
  version bumping and tagging are not `make` targets.

### 🔬 Running the Experiments

Each `ExperimentN.py` notebook is a self-contained CTA strategy. To search its
parameter space for the configuration that maximizes the portfolio Sharpe ratio,
run the Optuna driver in `book/marimo/helpers/optimize.py`:

```bash
# Optimize a single experiment (1–5) with an explicit trial budget
uv run python book/marimo/helpers/optimize.py --experiment 3 --trials 200

# Optimize all five, each with its per-experiment default budget
uv run python book/marimo/helpers/optimize.py --experiment all

# Reproducible run with Optuna's per-trial logging (short flags)
uv run python book/marimo/helpers/optimize.py -e 1 -n 50 --seed 7 --verbose
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
# Open the notebooks in book/marimo/notebooks in the marimo editor
make marimo

# Run every notebook as a script and report which ones fail
make marimo-validate
```

`make help` lists every available target.

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
