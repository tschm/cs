#!/usr/bin/env python3
"""Check that the tests mirror the marimo notebooks 1:1 (repo-local layout gate).

Why this exists (and why it is *not* the bundled Rhiza checker)
---------------------------------------------------------------
Rhiza ships a ``check_test_layout.py`` that assumes a ``src/<pkg>`` source tree.
This project has no ``src/``: its "source" is the set of marimo notebooks under
``book/marimo/notebooks``, and ``tests/`` mirrors *those*. Pointed at the default
``src/`` the bundled checker reports every test as an orphan even though real 1:1
parity is intact, so this repo ships its own gate that understands the actual
layout:

  * every notebook module ``book/marimo/notebooks/<Name>.py`` has a mirror test
    ``tests/test_<name>.py`` — matched case-insensitively, because the notebooks
    are TitleCased (``Experiment1.py`` <-> ``test_experiment1.py``);
  * every ``tests/test_*.py`` maps back to a notebook module, except the declared
    cross-cutting integration tests in ``INTEGRATION_TESTS``.

``test_notebook_sharpe.py`` is such an integration test: it executes *all* the
experiment notebooks end-to-end and asserts their Sharpe ratios, so it has no
single source module and is allow-listed rather than treated as an orphan.

Unlike the bundled checker this gate is deliberately file-level only. The project
exercises its classes (e.g. ``optimize.Experiment``) through plain pytest
functions rather than mirrored ``Test*`` classes, which is idiomatic pytest and
intentionally left unconstrained here.

Run it directly or via the ``check-test-layout`` pre-commit hook::

    python3 scripts/check_test_layout.py

Uses only the standard library, matching the other scripts in this folder.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "book" / "marimo" / "notebooks"
TESTS_DIR = ROOT / "tests"

# Test files that legitimately have no single source module: cross-cutting
# integration tests that drive several notebooks at once.
INTEGRATION_TESTS = {"test_notebook_sharpe.py"}

# Non-test helper modules under tests/ (imported by the tests, not test files
# themselves). ``test_*.py`` globbing already excludes these; listed for clarity.
_IGNORED = {"__init__.py", "conftest.py"}


def _notebook_modules() -> dict[str, Path]:
    """Return ``{lowercased stem: path}`` for every notebook module (flat layout)."""
    return {path.stem.lower(): path for path in sorted(NOTEBOOK_DIR.glob("*.py")) if path.name not in _IGNORED}


def _test_files() -> list[Path]:
    """Return the ``test_*.py`` files under ``tests/`` (ignoring conftest)."""
    return sorted(path for path in TESTS_DIR.glob("test_*.py") if path.name not in _IGNORED)


def _missing_mirror_tests(notebooks: dict[str, Path]) -> list[str]:
    """Forward check: every notebook module needs a mirror ``test_<name>.py``."""
    return [
        f"missing test file tests/test_{stem}.py for notebook {module.relative_to(ROOT)}"
        for stem, module in notebooks.items()
        if not (TESTS_DIR / f"test_{stem}.py").exists()
    ]


def _orphan_test_files(notebooks: dict[str, Path]) -> list[str]:
    """Reverse check: every test file maps to a notebook module or an integration test."""
    orphans = []
    for test_file in _test_files():
        stem = test_file.stem[len("test_") :]
        if test_file.name not in INTEGRATION_TESTS and stem not in notebooks:
            orphans.append(
                f"orphan test file {test_file.relative_to(ROOT)} "
                f"(no notebook {NOTEBOOK_DIR.relative_to(ROOT)}/{stem}.py, "
                f"and not listed in INTEGRATION_TESTS)"
            )
    return orphans


def check() -> list[str]:
    """Return a list of layout violations (empty when the layout is clean)."""
    notebooks = _notebook_modules()
    return _missing_mirror_tests(notebooks) + _orphan_test_files(notebooks)


def main() -> int:
    """Check the notebook/test layout and return an exit code."""
    errors = check()
    if errors:
        print("Test-layout check failed:", file=sys.stderr)
        for err in errors:
            print(f"  ✗ {err}", file=sys.stderr)
        return 1
    print("Test layout OK: tests mirror the marimo notebooks 1:1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
