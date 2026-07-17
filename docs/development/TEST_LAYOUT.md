# Test-layout parity

Rhiza enforces a strict 1:1 parity between source modules and tests, so a test is
always easy to locate from the code it covers. The bundled checker
(`check_test_layout.py`) assumes a `src/<pkg>` source tree and maps
`src/…/xyz.py` to `tests/…/test_xyz.py`.

## Why this repo deviates

This project has **no `src/` directory**. Its "source" is the set of marimo
notebooks under `book/marimo/notebooks/`, and `tests/` mirrors *those*:

| Notebook (`book/marimo/notebooks/`) | Mirror test (`tests/`) |
| --- | --- |
| `Experiment1.py` … `Experiment5.py` | `test_experiment1.py` … `test_experiment5.py` |
| `optimize.py` | `test_optimize.py` |
| `preamble.py` | `test_preamble.py` |

Pointed at the default `src/`, the bundled checker reports every one of these
tests as an orphan even though real parity is intact. Two further facts make the
stock checker a poor fit here:

- **TitleCased notebooks.** The notebooks are `Experiment1.py`, but their tests
  are `test_experiment1.py`; the mapping has to be case-insensitive.
- **A cross-cutting integration test.** `tests/test_notebook_sharpe.py` executes
  *all* the experiment notebooks end-to-end and asserts their Sharpe ratios. It
  has no single source module by design, so it must be allow-listed rather than
  flagged as an orphan.

## The repo-local gate

Rather than disable the check, this repo ships its own layout gate,
[`scripts/check_test_layout.py`](../../scripts/check_test_layout.py), that
understands the real structure. It verifies that:

- every notebook module has a mirror `tests/test_<name>.py` (matched
  case-insensitively); and
- every `tests/test_*.py` maps back to a notebook module, except the declared
  cross-cutting integration tests (`INTEGRATION_TESTS`).

It is deliberately **file-level only**: the project exercises its classes (e.g.
`optimize.Experiment`) through plain pytest functions rather than mirrored
`Test*` classes, which is idiomatic pytest.

Run it directly, or let the `check-test-layout` pre-commit hook run it whenever a
notebook or test file changes:

```bash
python3 scripts/check_test_layout.py
```

When you add a notebook, add its mirror test in the same commit. When you add a
test that legitimately spans several notebooks, add it to `INTEGRATION_TESTS` in
the gate with a one-line note on what it covers.
