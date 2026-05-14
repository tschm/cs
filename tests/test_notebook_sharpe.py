import math
import re
import runpy
import signal
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = (ROOT / "book" / "marimo" / "notebooks").resolve()
FLOAT_PATTERN = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
NOTEBOOKS = sorted(path.resolve() for path in NOTEBOOK_DIR.glob("*.py"))
NOTEBOOK_TIMEOUT = 600


def _run_notebook(notebook: Path) -> str:
    """Execute a notebook in-process and return its stdout."""
    stdout = StringIO()
    stderr = StringIO()

    def _timeout_handler(_signum: int, _frame: object) -> None:
        msg = f"Notebook execution timed out after {NOTEBOOK_TIMEOUT}s: {notebook}"
        raise TimeoutError(msg)

    previous = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(NOTEBOOK_TIMEOUT)
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            runpy.run_path(str(notebook), run_name="__main__")
    except Exception as exc:
        message = stderr.getvalue() or str(exc)
        pytest.fail(f"Notebook failed: {notebook}\n{message}")
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)

    return stdout.getvalue()


def _extract_sharpe_ratio(output: str) -> float:
    """Return the final numeric value printed by a notebook as its Sharpe ratio."""
    matches = FLOAT_PATTERN.findall(output)
    if not matches:
        pytest.fail(f"Notebook output did not contain a Sharpe ratio:\n{output}")
    return float(matches[-1])


def _trusted_notebook_path(notebook: Path) -> Path:
    """Return a validated repo-local notebook path for in-process execution."""
    notebook = notebook.resolve()
    if not notebook.is_relative_to(NOTEBOOK_DIR):
        msg = f"Notebook must be within {NOTEBOOK_DIR}: {notebook}"
        raise ValueError(msg)
    if notebook.suffix != ".py":
        msg = f"Unexpected notebook path: {notebook}"
        raise ValueError(msg)
    return notebook


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda path: path.stem)
def test_notebook_computes_finite_sharpe_ratio(
    notebook: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("marimo")
    notebook = _trusted_notebook_path(notebook)
    output_dir = tmp_path / notebook.stem
    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("NOTEBOOK_OUTPUT_FOLDER", str(output_dir))

    sharpe_ratio = _extract_sharpe_ratio(_run_notebook(notebook))

    assert math.isfinite(sharpe_ratio)
