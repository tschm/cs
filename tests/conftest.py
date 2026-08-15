"""Shared pytest fixtures for experiment signal function tests.

Security Notes:
- S101 (assert usage): Asserts are used in pytest tests to validate conditions.
- Test code operates in a controlled environment with trusted inputs.
"""

import sys
from pathlib import Path

import pytest

# Bootstrap the notebook directory onto sys.path once, here, so every test
# module can ``from preamble import load_notebook`` (the shared notebook loader)
# instead of repeating its own ``sys.path`` + ``runpy`` boilerplate. The
# notebooks are not an importable package, so this single insert is the price of
# reaching their shared ``preamble`` helper module.
NOTEBOOK_DIR = (Path(__file__).resolve().parents[1] / "book" / "marimo" / "notebooks").resolve()
if str(NOTEBOOK_DIR) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_DIR))

# The repo-local gate scripts are standalone stdlib modules, not a package, so
# they need the same treatment to be importable by their unit tests.
SCRIPTS_DIR = (Path(__file__).resolve().parents[1] / "scripts").resolve()
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

N = 600  # satisfies min_samples=300 (the highest requirement across all experiments)


# polars is imported inside the fixtures rather than at module level so this
# conftest stays loadable in an environment that has only pytest. The gate-script
# tests (tests/test_check_*.py) exercise stdlib-only modules and run in exactly
# such an environment — the "scripts/ unit tests at 100% coverage" pre-commit
# hook, which prek provisions with pytest alone. A module-level import would make
# collecting them require the whole scientific stack, purely to reach the
# sys.path bootstrap above. Every fixture below is requested only by tests that
# already depend on polars, so the import always resolves where it is used.
@pytest.fixture
def rising():
    """Return a DataFrame with a monotonically rising price series."""
    import polars as pl

    return pl.DataFrame({"p": [float(i) for i in range(1, N + 1)]})


@pytest.fixture
def falling():
    """Return a DataFrame with a monotonically falling price series."""
    import polars as pl

    return pl.DataFrame({"p": [float(i) for i in range(N, 0, -1)]})
