"""Fuzz the CTA experiment signal functions against arbitrary numeric input.

Each ``ExperimentN.py`` marimo notebook exposes a module-level signal function
``f(price, ...)`` that maps a polars price expression and a handful of numeric
parameters (``fast``/``slow``/``vola``/``clip``/``volatility``) to a position
signal expression. These functions are the numeric core of the project: there is
no string/bytes/config parser surface to fuzz, so this harness synthesizes a
price series and parameter set from arbitrary bytes and drives every ``f``
through the same ``DataFrame.select`` evaluation path the notebooks use. It
asserts each function either evaluates or rejects the input with a documented
exception (a parameter ``ValueError``/``TypeError`` or a ``polars.PolarsError``
from the lazy compute layer) — never an unexpected crash.

Run locally:
    RHIZA_FUZZ_ROOT=$(pwd) pip install atheris
    RHIZA_FUZZ_ROOT=$(pwd) python tests/fuzz/fuzz_signal.py -atheris_runs=10000

Run in ClusterFuzzLite: this file is built by .clusterfuzzlite/build.sh.
"""

from __future__ import annotations

import contextlib
import math
import os
import sys
from pathlib import Path

import atheris

# When running from the source tree (local development), add the marimo notebook
# directory to sys.path so the ``ExperimentN`` modules (which define ``f``)
# import without installation. This repo is not src-layout: the importable
# modules are flat files under book/marimo/notebooks, exactly the directory the
# project's own tests put on sys.path. In ClusterFuzzLite, build.sh runs
# `pip install .` to provide the runtime deps (numpy/polars/jquantstats/tinycta)
# and copies the repo into the frozen binary, so these modules resolve there too.
_REPO_ROOT = Path(os.environ.get("RHIZA_FUZZ_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
_NOTEBOOK_DIR = str(_REPO_ROOT / "book" / "marimo" / "notebooks")
if _NOTEBOOK_DIR not in sys.path:
    sys.path.insert(0, _NOTEBOOK_DIR)

import Experiment1  # noqa: E402
import Experiment2  # noqa: E402
import Experiment3  # noqa: E402
import Experiment4  # noqa: E402
import Experiment5  # noqa: E402
import polars as pl  # noqa: E402
from polars.exceptions import PolarsError  # noqa: E402

# Documented rejections of malformed input:
#   * ValueError  — the EWM parameters reject non-positive ``com`` (a negative
#     fast/slow/vola/volatility), and "one of com/span/half_life/alpha must be
#     set" when a parameter is None.
#   * TypeError   — a non-numeric parameter fails the parameter comparisons /
#     unary-minus inside the polars and tinycta call paths.
#   * PolarsError — the lazy compute layer (ComputeError, InvalidOperationError,
#     SchemaError, ShapeError, ...) rejects a degenerate series/expression.
# Any other exception is a genuine crash and is allowed to propagate.
_EXPECTED_SIGNAL_ERRORS = (ValueError, TypeError, PolarsError)

# The smallest sensible series; tinycta's vol_adj/osc paths (Experiments 3-5) use
# min_samples up to 300, so a short series simply yields nulls rather than error.
_MIN_ROWS = 2
_MAX_ROWS = 512


def test_one_input(data: bytes) -> None:
    """Build a price series and parameters from bytes, then evaluate each signal ``f``."""
    fdp = atheris.FuzzedDataProvider(data)

    n_rows = _MIN_ROWS + fdp.ConsumeIntInRange(0, _MAX_ROWS - _MIN_ROWS)
    prices = [fdp.ConsumeRegularFloat() for _ in range(n_rows)]
    # A column that is entirely non-finite carries no signal and only exercises
    # numpy/polars NaN handling, which is not the surface under test; skip it.
    if not any(math.isfinite(value) for value in prices):
        return
    frame = pl.DataFrame({"p": prices})

    # Parameters span the notebook slider ranges and then some, including the
    # adversarial out-of-range / degenerate values the documented exceptions cover.
    fast = fdp.ConsumeIntInRange(-8, 256)
    slow = fdp.ConsumeIntInRange(-8, 256)
    vola = fdp.ConsumeIntInRange(-8, 256)
    volatility = fdp.ConsumeIntInRange(-8, 256)
    clip = fdp.ConsumeRegularFloat()

    targets = (
        (Experiment1.f, {"fast": fast, "slow": slow}),
        (Experiment2.f, {"fast": fast, "slow": slow, "volatility": volatility}),
        (Experiment3.f, {"fast": fast, "slow": slow, "vola": vola, "clip": clip}),
        (Experiment4.f, {"fast": fast, "slow": slow, "vola": vola, "clip": clip}),
        (Experiment5.f, {"fast": fast, "slow": slow, "vola": vola, "clip": clip}),
    )
    for signal, kwargs in targets:
        with contextlib.suppress(_EXPECTED_SIGNAL_ERRORS):
            frame.select(signal(pl.col("p"), **kwargs))


def main() -> None:
    """Run the Atheris fuzz loop."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
