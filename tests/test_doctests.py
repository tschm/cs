"""Execute the doctest examples embedded in the hand-written notebook modules.

Why this test exists
--------------------
``make docs-coverage`` (interrogate) asks whether a docstring *exists*; until this
module, nothing in the repo asked whether what a docstring *claims* is still true.
That is the documentation failure with the longest half-life: an example whose
output has drifted keeps rendering perfectly and keeps passing every other gate,
and the person who finds out is a newcomer following the README.

The template's own docstring gate does not close the gap here. ``.rhiza/tests/
test_docstrings.py`` looks for a ``src/`` tree, and this project has none — its
source is the marimo notebook set under ``book/marimo/notebooks`` — so it skips
outright rather than checking anything.

Scope
-----
The four hand-written modules: ``preamble.py`` and ``optimize.py`` under
``book/marimo/notebooks``, plus the two repo-local gate scripts under ``scripts/``.
All four are ordinary Python whose docstrings are durable.

The ``Experiment*.py`` notebooks are excluded because they are marimo-generated, and
the reasoning that exempts their generated cell scaffolding from ``[tool.mypy]``
applies equally to examples embedded in them: marimo would wipe them on the next
rewrite, so they buy no lasting safety. Those notebooks are pinned end-to-end by
``test_notebook_sharpe.py`` instead.

``conftest.py`` puts both the notebook directory and ``scripts/`` on ``sys.path``, so
all four modules import here exactly as they do for every other test in this suite.

Note that the gate scripts are stdlib-only and are additionally unit-tested to 100%
by the "scripts/ unit tests at 100% coverage" pre-commit hook, which runs in a
pytest-only environment. This module is *not* part of that hook's set — it imports
``optimize``/``preamble`` and so needs the full scientific stack — which is why the
doctests here add no dependency burden to that lightweight gate.
"""

import doctest
from types import ModuleType

import check_inline_pins
import check_test_layout
import optimize
import preamble
import pytest

MODULES = [preamble, optimize, check_inline_pins, check_test_layout]


@pytest.mark.parametrize("module", MODULES, ids=lambda module: module.__name__)
def test_docstring_examples_produce_their_documented_output(module: ModuleType) -> None:
    """Every ``>>>`` example in the module runs and returns what it says it returns."""
    results = doctest.testmod(module, verbose=False)
    assert results.failed == 0, (
        f"{results.failed} of {results.attempted} doctest example(s) failed in "
        f"{module.__name__}; see the diff printed above"
    )


@pytest.mark.parametrize("module", MODULES, ids=lambda module: module.__name__)
def test_module_actually_carries_examples(module: ModuleType) -> None:
    """Guard against a vacuous pass: a module with no examples must not look green.

    ``doctest.testmod`` reports success on a module containing nothing to run, so
    without this assertion the gate above would silently stop meaning anything the
    moment an example was deleted.
    """
    found = sum(len(test.examples) for test in doctest.DocTestFinder().find(module))
    assert found > 0, f"{module.__name__} carries no doctest examples"
