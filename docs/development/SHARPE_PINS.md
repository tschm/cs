# Sharpe-ratio regression pins

The test suite pins the Sharpe ratio of every experiment notebook to six
decimal places. The pinned values live in **one place**:

```text
tests/expected_sharpe.py
```

Two test modules read from it:

- `tests/test_notebook_sharpe.py` executes each notebook end-to-end in a
  subprocess and compares the printed Sharpe ratio against the pin.
- `tests/test_optimize.py` rebuilds each strategy through the `build_exp*`
  functions in `book/marimo/notebooks/optimize.py` and checks they reproduce
  the same numbers, so the optimizer's builders cannot silently diverge from
  the notebooks.

## Why the tolerance is so tight

The 1e-6 relative/absolute tolerance is deliberate. The notebooks are the
deliverable of this project, and their headline numbers are quoted in the
accompanying book. Any change to strategy logic — or any dependency upgrade
that perturbs floating-point results — should fail loudly rather than slip
through.

## When a dependency bump breaks the pins

Renovate/Dependabot PRs occasionally fail these tests because a new
numpy/polars/jquantstats release changes results in the last few digits.
That is the test doing its job. To review and update:

1. Check out the failing branch and run the suite to see old vs. new values:

   ```bash
   uv run pytest tests/test_notebook_sharpe.py tests/test_optimize.py -v
   ```

   The assertion message prints the expected pin and the freshly computed
   value side by side.

2. **Eyeball the deltas.** Differences in the 6th decimal place or beyond are
   harmless floating-point churn. A change in the first couple of decimals
   means the dependency altered actual behaviour — investigate before
   accepting it (read the dependency's changelog; bisect the bump if needed).

3. If the deltas are acceptable, copy the new values into
   `EXPECTED_SHARPE_RATIOS` in `tests/expected_sharpe.py` and note the cause
   in the commit message (e.g. "re-pin Sharpe baselines for numpy 2.5
   summation-order change").

4. Re-run the full suite; both test modules must agree on the new pins. If
   only the notebook tests moved but the optimizer builders did not (or vice
   versa), the two code paths have genuinely diverged — fix that instead of
   re-pinning.

Never widen the tolerances to make a bump pass; that trades away the
regression protection the pins exist to provide.
