"""Unit tests for the repo-local PEP 723 inline-pin gate.

Why these exist
---------------
``scripts/check_inline_pins.py`` guarantees that the ``# /// script`` pins in the
marimo notebooks agree with ``uv.lock``. It runs as a pre-commit hook, so it
*executes* on every relevant commit — but until this module nothing verified that
it still *detects* anything. A glob that stopped matching, or a regex that stopped
firing, would leave the hook passing silently while the guarantee was gone.

The Sharpe-ratio regression tests pin results to 1e-6, and they only mean anything
if the notebook environment and the locked environment agree. That makes a silent
failure of this gate expensive, which is why it gets tests of its own.

Every test drives the module through monkeypatched ``ROOT`` / ``NOTEBOOK_DIR``
globals against a temporary tree, so nothing here depends on the repository's real
notebooks or lockfile.
"""

from pathlib import Path

import check_inline_pins
import pytest

HEADER = """\
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "numpy=={numpy}",
#     "polars=={polars}",
# ]
# ///

\"\"\"A notebook.\"\"\"
"""


def _write_lock(root: Path, packages: dict[str, str]) -> None:
    """Write a minimal uv.lock carrying ``packages`` into ``root``."""
    entries = "\n".join(f'[[package]]\nname = "{name}"\nversion = "{version}"\n' for name, version in packages.items())
    (root / "uv.lock").write_text(entries)


def _write_notebook(directory: Path, name: str, body: str) -> Path:
    """Write ``body`` to ``directory/name`` and return the path."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(body)
    return path


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """Point the module at a temporary root/notebook directory pair."""
    notebooks = tmp_path / "book" / "marimo" / "notebooks"
    notebooks.mkdir(parents=True)
    monkeypatch.setattr(check_inline_pins, "ROOT", tmp_path)
    monkeypatch.setattr(check_inline_pins, "NOTEBOOK_DIR", notebooks)
    return tmp_path, notebooks


def test_locked_versions_reads_every_package(tree):
    """locked_versions returns one lowercased entry per package in uv.lock."""
    root, _ = tree
    _write_lock(root, {"NumPy": "2.4.6", "polars": "1.43.2"})

    assert check_inline_pins.locked_versions() == {"numpy": "2.4.6", "polars": "1.43.2"}


def test_header_pins_reads_the_declared_pins(tree):
    """Each ``name==version`` line in the PEP 723 header is returned."""
    _, notebooks = tree
    notebook = _write_notebook(notebooks, "Experiment1.py", HEADER.format(numpy="2.4.6", polars="1.43.2"))

    assert check_inline_pins.header_pins(notebook) == {"numpy": "2.4.6", "polars": "1.43.2"}


def test_header_pins_stops_at_the_terminator(tree):
    """A pin-shaped comment in the file *body* is not mistaken for a header pin.

    This is the regression test for issue #518. The scan used to break at the
    ``# ///`` terminator only once it had already collected a pin, so a header
    declaring none fell through and kept reading the rest of the file.
    """
    _, notebooks = tree
    body = '# /// script\n# requires-python = ">=3.12"\n# ///\n\n# "numpy==9.9.9"\n'
    notebook = _write_notebook(notebooks, "Experiment1.py", body)

    assert check_inline_pins.header_pins(notebook) == {}


def test_notebook_drift_is_empty_when_pins_agree(tree):
    """A notebook whose pins match the lock produces no drift messages."""
    _, notebooks = tree
    notebook = _write_notebook(notebooks, "Experiment1.py", HEADER.format(numpy="2.4.6", polars="1.43.2"))

    assert check_inline_pins.notebook_drift(notebook, {"numpy": "2.4.6", "polars": "1.43.2"}) == []


def test_notebook_drift_reports_a_version_mismatch(tree):
    """A pin disagreeing with the lock is reported with both versions."""
    _, notebooks = tree
    notebook = _write_notebook(notebooks, "Experiment1.py", HEADER.format(numpy="2.4.6", polars="1.43.2"))

    messages = check_inline_pins.notebook_drift(notebook, {"numpy": "2.0.0", "polars": "1.43.2"})

    assert len(messages) == 1
    assert "numpy==2.4.6 (inline)" in messages[0]
    assert "numpy==2.0.0 (uv.lock)" in messages[0]


def test_notebook_drift_reports_a_package_absent_from_the_lock(tree):
    """A pin naming a package the lock does not resolve is reported."""
    _, notebooks = tree
    notebook = _write_notebook(notebooks, "Experiment1.py", HEADER.format(numpy="2.4.6", polars="1.43.2"))

    messages = check_inline_pins.notebook_drift(notebook, {"numpy": "2.4.6"})

    assert len(messages) == 1
    assert "'polars' is pinned inline but absent from uv.lock" in messages[0]


def test_main_returns_zero_when_every_pin_agrees(tree):
    """Exit code 0 when no notebook has drifted."""
    root, notebooks = tree
    _write_lock(root, {"numpy": "2.4.6", "polars": "1.43.2"})
    _write_notebook(notebooks, "Experiment1.py", HEADER.format(numpy="2.4.6", polars="1.43.2"))

    assert check_inline_pins.main() == 0


def test_main_returns_one_and_names_the_drift(tree, capsys):
    """Exit code 1, naming the offending notebook and the fix."""
    root, notebooks = tree
    _write_lock(root, {"numpy": "2.4.6", "polars": "1.43.2"})
    _write_notebook(notebooks, "Experiment3.py", HEADER.format(numpy="1.0.0", polars="1.43.2"))

    assert check_inline_pins.main() == 1

    stderr = capsys.readouterr().err
    assert "Experiment3.py" in stderr
    assert "Update the '# /// script' headers to match uv.lock." in stderr
