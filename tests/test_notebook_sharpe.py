import math
import os
import re
import shutil
import subprocess  # nosec B404 - tests invoke trusted, repo-local notebooks via uv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = (ROOT / "book" / "marimo" / "notebooks").resolve()
FLOAT_PATTERN = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
NOTEBOOKS = sorted(path.resolve() for path in NOTEBOOK_DIR.glob("*.py"))
NOTEBOOK_TIMEOUT = 600


def _extract_sharpe_ratio(output: str) -> float:
    """Return the final numeric value printed by a notebook as its Sharpe ratio."""
    matches = FLOAT_PATTERN.findall(output)
    if not matches:
        pytest.fail(f"Notebook output did not contain a Sharpe ratio:\n{output}")
    return float(matches[-1])


def _trusted_notebook_path(notebook: Path) -> Path:
    """Return a validated repo-local notebook path for subprocess execution."""
    notebook = notebook.resolve()
    if not notebook.is_relative_to(NOTEBOOK_DIR):
        msg = f"Notebook must be within {NOTEBOOK_DIR}: {notebook}"
        raise ValueError(msg)
    if notebook.suffix != ".py":
        msg = f"Unexpected notebook path: {notebook}"
        raise ValueError(msg)
    return notebook


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda path: path.stem)
def test_notebook_computes_finite_sharpe_ratio(notebook: Path, tmp_path: Path) -> None:
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.skip("uv is required to execute Marimo notebooks")

    notebook = _trusted_notebook_path(notebook)
    output_dir = tmp_path / notebook.stem
    env = {
        **os.environ,
        "NOTEBOOK_OUTPUT_FOLDER": str(output_dir),
    }
    result = subprocess.run(  # nosec B603 - argv is fixed and notebook path is validated above
        [uv_bin, "run", "--script", str(notebook)],
        capture_output=True,
        check=False,
        cwd=ROOT,
        env=env,
        text=True,
        timeout=NOTEBOOK_TIMEOUT,
    )

    assert result.returncode == 0, result.stderr

    sharpe_ratio = _extract_sharpe_ratio(result.stdout)

    assert math.isfinite(sharpe_ratio)
