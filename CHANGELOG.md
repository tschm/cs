## [1.2.1] - 2026-06-10

### 💼 Other

- Bump version 1.2.0 → 1.2.1

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md for v1.2.0 [skip ci]
## [1.2.0] - 2026-06-08

### 🚀 Features

- Add profiles: github-project to template.yml

### 🐛 Bug Fixes

- Resolve make fmt failures and CI security checks
- Downgrade polars constraint after 1.41.0 yanked from PyPI
- Align pyproject.toml with rhiza test requirements

### 💼 Other

- Bump version 1.1.0 → 1.2.0

### ⚙️ Miscellaneous Tasks

- Bump Rhiza template to v0.10.9
- Sync Rhiza template to v0.10.9
- Update rhiza template config and ignore notebook HTML outputs
- Restore template files and update lock after rhiza sync
- Bump rhiza template to v0.11.0
- Sync with rhiza v0.11.0
- Bump rhiza template to v0.13.3
- Sync with rhiza v0.13.3
- Bump rhiza to v0.15.1
- Apply rhiza sync v0.15.1
- Bump rhiza to v0.15.2
- Apply rhiza sync v0.15.2
- Bump rhiza to v0.15.3
- Apply rhiza sync v0.15.3
- Bump rhiza to v0.17.0
- Apply rhiza sync v0.17.0
- Bump rhiza to v0.18.4
- Apply rhiza sync v0.18.4
- Add pip dependabot entry for .rhiza/requirements
- Bump rhiza to v0.18.8
- Refactor CI workflows and expand test coverage for rhiza v0.18.8
## [1.1.0] - 2026-05-16

### 🚀 Features

- List individual notebooks in mkdocs nav

### 🐛 Bug Fixes

- *(notebooks)* Restore baseline Sharpe ratios in Experiment3 and Experiment4
- *(notebooks)* Suppress divide-by-zero warning in Experiment4 norm step
- *(tests)* Correct Sharpe ratio baselines for Experiment4 and Experiment5 after rebase
- *(tests)* Exclude preamble.py from notebook test collection
- *(notebooks)* Use portfolio.returns["returns"] for Sharpe computation

### 💼 Other

- Align notebook runtime dependencies
- *(notebooks)* Remove stale imports and redundant comments
- *(deps)* Bump jquantstats to v0.8.3
- *(deps)* Bump jquantstats to v0.8.3 in notebooks
- Lower Python version requirement to >=3.11 in pyproject.toml
- Sync uv.lock
- Bump version 1.0.0 → 1.1.0

### 🚜 Refactor

- *(notebooks)* Replace cvxsimulator with jquantstats in Experiment1, Experiment2, and Experiment3
- *(notebooks)* Replace cvxsimulator with jquantstats in Experiment4 and Experiment5
- *(notebooks)* Improve Sharpe ratio calculation in Experiment2 by using NAV-based method
- *(notebooks)* Update Sharpe ratio calculation in Experiment3 to use NAV-based method
- *(notebooks)* Improve Experiment5 by redefining `osc` and `returns_adjust` functions, updating Sharpe ratio calculation, and refactoring correlation logic
- *(notebooks)* Replace pandas with polars in Experiment4
- *(notebooks)* Enhance Experiment5 with Polars-based `osc_fn` and `returns_adjust`, optimize correlation workflow, and update Sharpe ratios in tests
- *(notebooks)* Replace pandas with polars in Experiment3
- *(notebooks)* Use analytical oscillator scaling from Experiment3 in Experiment4 and Experiment5
- *(notebooks)* Integrate TinyCTA vol_adj in Experiment3, remove custom filter function, and update Sharpe ratios in tests
- *(notebooks)* Replace custom osc with tinycta.osc and bump tinycta to 0.12.2
- *(notebooks)* Replace local osc/returns_adjust with tinycta in Experiment4 and Experiment5
- *(notebooks)* Make f an Expr->Expr function in Experiment1 and Experiment2
- *(notebooks)* Extract Expr->Expr function f in Experiment4 and Experiment5
- *(notebooks)* Use expr-based interface in Experiment1
- *(notebooks)* Use expr-based interface in Experiment2
- *(notebooks)* Use expr-based interface in Experiments 3, 4, and 5
- *(notebooks)* Extract price loading logic into reusable `preamble` module
- *(notebooks)* Tighten preamble — export only date_col and load_prices
- *(notebooks)* Precompute prices_only in setup, split Sharpe cell
- *(notebooks)* With_columns -> select for vol-adjusted returns in Experiment5
- Replace inline Sharpe ratio calculation with portfolio.stats.sharpe()

### 📚 Documentation

- Remove stale requirements.txt hint from README
- Add Rhiza infrastructure section to README
- Remove stale Jupyter Book reference from README
- Refresh MARIMO.md with actual project notebooks and structure
- *(notebooks)* Remove stale comments and outdated references

### ⚡ Performance

- *(Experiment3)* Use pl.all() and pl.concat to speed up Polars operations
- *(notebooks)* Replace per-column loops with pl.all() and pl.from_numpy across all experiments

### 🧪 Testing

- Add sharpe ratio notebook coverage
- Tidy notebook timeout constant
- Document notebook sharpe parsing
- Harden notebook subprocess invocation
- Clarify notebook path guard
- Use explicit notebook trust check
- Run notebooks in process
- Use process timeout for notebooks
- Polish notebook process runner
- Document notebook process execution
- Harden notebook process shutdown
- Clarify notebook runtime checks
- Clarify notebook timeout handling
- Hardcode notebook sharpe baselines
- Relax sharpe baseline tolerance
- Check sharpe baselines cover notebooks
- Name sharpe tolerance constants
- Update Sharpe ratio baselines for profit/AUM return convention
- *(preamble)* Add test suite for preamble.py
- *(experiment1)* Add unit tests for signal function f
- Add test suites for preamble and experiments 2–5
- Cache load_prices dataframe in preamble tests

### ⚙️ Miscellaneous Tasks

- Prepare rhiza sync infrastructure
- Sync with rhiza template v0.9.5
- Bump Rhiza template to v0.10.2
- Sync Rhiza template to v0.10.2
- Add mkdocs.yml based on docs/mkdocs-base.yml
- Merge main into rhiza, resolve all conflicts
- Remove direct pandas dependency references
- *(notebooks)* Bump tinycta to 0.12.1 in Experiment3, Experiment4, and Experiment5
- Bump tinycta to 0.12.1 in pyproject.toml and uv.lock
- Add CI workflow for tests across Python 3.11–3.14 and all OSes
- Remove commented-out Docker config from dependabot.yml
## [1.0.0] - 2026-01-28

### 💼 Other

- Bump version 0.0.0 → 1.0.0

### ⚙️ Miscellaneous Tasks

- Sync config files from .config-templates (#286)
- Sync config files from .config-templates (#287)
- Sync config files from .config-templates (#289)
- Sync config files from .config-templates (#292)
- Sync config files from .config-templates (#295)
- Sync config files from .config-templates (#297)
- Sync config files from .config-templates (#300)
- Sync template files (#301)
- Sync template files (#303)
- Sync template files (#304)
- Sync template files (#305)
- Sync template files (#308)
- Sync template files (#314)
- Sync template files (#316)
- Sync template files (#320)
- Sync template files (#321)
- Sync template files
- Sync template files
- Sync template files
- Sync template files
- Sync template files
- Sync template files
- Sync template files
- Remove deprecated files
- Import rhiza templates
- Import rhiza templates
- Update via rhiza
- Update via rhiza
- Import rhiza templates
- Update via rhiza
- Update via rhiza
- Remove unused dependencies
- Update lockfile
## [0.0.5] - 2025-05-25

### ⚙️ Miscellaneous Tasks

- *(config)* Migrate config .github/renovate.json (#210)
## [list] - 2019-05-01
