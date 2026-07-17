#!/usr/bin/env python3
"""Check that notebook PEP 723 inline pins match the versions resolved in uv.lock.

The marimo notebooks under ``book/marimo/notebooks`` carry ``# /// script``
metadata so they can be run standalone with ``uv run``. The repository test
suite, however, runs against the environment resolved in ``uv.lock`` — and the
Sharpe-ratio regression tests pin results to 1e-6, so a version drift between
the two environments silently invalidates what the tests guarantee.

This script fails (exit code 1) whenever a ``name==version`` pin in a notebook
header disagrees with the version locked in ``uv.lock``. Run it directly or via
the pre-commit hook of the same name:

    python3 scripts/check_inline_pins.py

Uses only the standard library so it can run anywhere Python 3.11+ is present.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "book" / "marimo" / "notebooks"
PIN_PATTERN = re.compile(r'^#\s*"(?P<name>[A-Za-z0-9._-]+)==(?P<version>[^"]+)"')
HEADER_END = "# ///"


def locked_versions() -> dict[str, str]:
    """Return {package: version} for every package resolved in uv.lock."""
    with (ROOT / "uv.lock").open("rb") as handle:
        lock = tomllib.load(handle)
    return {package["name"].lower(): package["version"] for package in lock["package"]}


def header_pins(notebook: Path) -> dict[str, str]:
    """Return {package: version} for the ``name==version`` pins in a notebook header."""
    pins: dict[str, str] = {}
    for line in notebook.read_text().splitlines():
        if line.strip() == HEADER_END and pins:
            break
        match = PIN_PATTERN.match(line.strip())
        if match:
            pins[match["name"].lower()] = match["version"]
    return pins


def notebook_drift(notebook: Path, locked: dict[str, str]) -> list[str]:
    """Return the drift messages for one notebook's inline pins against ``locked``."""
    messages = []
    for name, pinned in header_pins(notebook).items():
        resolved = locked.get(name)
        if resolved is None:
            messages.append(f"{notebook.name}: '{name}' is pinned inline but absent from uv.lock")
        elif resolved != pinned:
            messages.append(f"{notebook.name}: {name}=={pinned} (inline) != {name}=={resolved} (uv.lock)")
    return messages


def main() -> int:
    """Compare every notebook's inline pins against uv.lock and report drift."""
    locked = locked_versions()
    failures = [msg for notebook in sorted(NOTEBOOK_DIR.glob("*.py")) for msg in notebook_drift(notebook, locked)]
    if failures:
        print("Notebook inline script pins have drifted from uv.lock:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print("Update the '# /// script' headers to match uv.lock.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
