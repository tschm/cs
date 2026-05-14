import math
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "book" / "marimo" / "notebooks"
FLOAT_PATTERN = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
NOTEBOOKS = sorted(NOTEBOOK_DIR.glob("*.py"))


def _extract_sharpe_ratio(output: str) -> float:
    matches = FLOAT_PATTERN.findall(output)
    if not matches:
        pytest.fail(f"Notebook output did not contain a Sharpe ratio:\n{output}")
    return float(matches[-1])


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda path: path.stem)
def test_notebook_computes_finite_sharpe_ratio(notebook: Path, tmp_path: Path) -> None:
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.skip("uv is required to execute Marimo notebooks")

    output_dir = tmp_path / notebook.stem
    env = {
        **os.environ,
        "NOTEBOOK_OUTPUT_FOLDER": str(output_dir),
    }
    result = subprocess.run(
        [uv_bin, "run", "--script", str(notebook)],
        capture_output=True,
        check=False,
        cwd=ROOT,
        env=env,
        text=True,
        timeout=600,
    )

    assert result.returncode == 0, result.stderr

    sharpe_ratio = _extract_sharpe_ratio(result.stdout)

    assert math.isfinite(sharpe_ratio)
