## .rhiza/make.d/custom-env.mk - Custom Environment Configuration
# This file example shows how to set variables for the project.
#
# This file is locally owned (see the `exclude:` block in .rhiza/template.yml)
# so these overrides survive `rhiza` syncs.

# This repository is a marimo "book", not a src/ library: the importable
# modules and notebooks live under book/marimo/notebooks. Point the source
# folder there so `make typecheck`, `make docs-coverage` and the `make test`
# coverage gate run against the real code instead of skipping a missing src/.
# (.rhiza/make.d/*.mk is included after .rhiza/.env, so this wins over the
# template default SOURCE_FOLDER=src.)
SOURCE_FOLDER := book/marimo/notebooks

# Every executable line is covered (marimo's structural cell `return`s and the
# CLI guard are excluded in [tool.coverage.report]); hold the gate at 100.
COVERAGE_FAIL_UNDER ?= 100
