import math
import multiprocessing
import os
import re
import runpy
import traceback
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from queue import Empty

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = (ROOT / "book" / "marimo" / "notebooks").resolve()
FLOAT_PATTERN = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
NOTEBOOKS = sorted(path.resolve() for path in NOTEBOOK_DIR.glob("*.py"))
EXPECTED_SHARPE_RATIOS = {
    "Experiment1": 0.7819474087813011,
    "Experiment2": 1.1260755020625202,
    "Experiment3": 1.127579694747821,
    "Experiment4": 1.1358730785064524,
    "Experiment5": 1.3807276232244459,
}
NOTEBOOK_TIMEOUT = 600
# Queue read grace period after the child has exited and should have published a result.
QUEUE_TIMEOUT = 10
# Grace period for a timed-out child to exit after terminate() before escalating to kill().
PROCESS_CLEANUP_TIMEOUT = 10
# Short wait for a kill()ed child to disappear before failing the test.
PROCESS_KILL_TIMEOUT = 1
PROCESS_START_METHOD = "spawn"


def _run_notebook_worker(notebook: str, output_dir: str, queue: multiprocessing.Queue) -> None:
    """Execute a notebook and report its outcome through a multiprocessing queue.

    This runs in a child process, so changing its cwd or environment does not
    affect the parent pytest process.
    """
    stdout = StringIO()
    stderr = StringIO()
    try:
        os.chdir(ROOT)
        os.environ["NOTEBOOK_OUTPUT_FOLDER"] = output_dir
        with redirect_stdout(stdout), redirect_stderr(stderr):
            runpy.run_path(notebook, run_name="__main__")
    except Exception as exc:
        queue.put(
            {
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue(),
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        return

    queue.put({"stdout": stdout.getvalue(), "stderr": stderr.getvalue(), "error": None, "traceback": None})


def _run_notebook(notebook: Path, output_dir: Path) -> str:
    """Execute a notebook in a child process and return its stdout.

    The repository test environment installs the notebook runtime dependencies,
    so the generated Python script can be executed directly without relying on
    uv's inline script metadata handling during the test itself.
    """
    ctx = multiprocessing.get_context(PROCESS_START_METHOD)
    queue = ctx.Queue()
    process = ctx.Process(target=_run_notebook_worker, args=(str(notebook), str(output_dir), queue))
    process.start()
    process.join(timeout=NOTEBOOK_TIMEOUT)

    if process.exitcode is None:
        process.terminate()
        process.join(timeout=PROCESS_CLEANUP_TIMEOUT)
        if process.exitcode is None:
            process.kill()
            process.join(timeout=PROCESS_KILL_TIMEOUT)
        pytest.fail(f"Notebook execution timed out after {NOTEBOOK_TIMEOUT}s: {notebook}")

    try:
        result = queue.get(timeout=QUEUE_TIMEOUT)
    except Empty:
        pytest.fail(f"Notebook exited without output: {notebook}")

    if result["error"] is not None:
        message = f"{result['stderr']}\n{result['error']}" if result["stderr"] else result["error"]
        pytest.fail(f"Notebook failed: {notebook}\n{message}\n{result['traceback']}")

    return result["stdout"]


def _extract_sharpe_ratio(output: str) -> float:
    """Return the final numeric value printed by a notebook as its Sharpe ratio."""
    matches = FLOAT_PATTERN.findall(output)
    if not matches:
        pytest.fail(f"Notebook output did not contain a Sharpe ratio:\n{output}")
    return float(matches[-1])


def _trusted_notebook_path(notebook: Path) -> Path:
    """Return a validated repo-local notebook path for child-process execution."""
    notebook = notebook.resolve()
    if not notebook.is_relative_to(NOTEBOOK_DIR):
        msg = f"Notebook must be within {NOTEBOOK_DIR}: {notebook}"
        raise ValueError(msg)
    if notebook.suffix != ".py":
        msg = f"Unexpected notebook path: {notebook}"
        raise ValueError(msg)
    return notebook


def test_expected_sharpe_ratio_baselines_cover_all_notebooks() -> None:
    assert set(EXPECTED_SHARPE_RATIOS) == {notebook.stem for notebook in NOTEBOOKS}


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda path: path.stem)
def test_notebook_matches_expected_sharpe_ratio(
    notebook: Path,
    tmp_path: Path,
) -> None:
    pytest.importorskip("marimo", reason="Marimo notebooks import marimo at module import time")
    notebook = _trusted_notebook_path(notebook)
    output_dir = tmp_path / notebook.stem
    expected_sharpe_ratio = EXPECTED_SHARPE_RATIOS[notebook.stem]

    sharpe_ratio = _extract_sharpe_ratio(_run_notebook(notebook, output_dir))

    assert math.isfinite(sharpe_ratio)
    assert sharpe_ratio == pytest.approx(expected_sharpe_ratio, rel=1e-6, abs=1e-6)
