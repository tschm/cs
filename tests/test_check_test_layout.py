"""Unit tests for the repo-local test-layout parity gate.

Why these exist
---------------
``scripts/check_test_layout.py`` is the reason this project can set
``enforce = false`` on the generic ``[tool.check_test_layout]`` checker: it is the
gate that actually understands the notebook layout. It runs as a pre-commit hook,
but until this module nothing verified that it still *detects* a violation. A
gate that silently stops failing is worse than no gate, because the opt-out in
``pyproject.toml`` points at it as the compensating control.

Note the bootstrapping problem this module had to solve first (issue #516): the
checker's own reverse pass treats any ``tests/test_<x>.py`` without a matching
notebook ``<x>.py`` as an orphan, so this very file was a violation until it was
added to ``SCRIPT_TESTS``.

Every test drives the module through monkeypatched ``ROOT`` / ``NOTEBOOK_DIR`` /
``TESTS_DIR`` globals against a temporary tree.
"""

import check_test_layout
import pytest


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """Point the module at an empty temporary notebook/tests directory pair."""
    notebooks = tmp_path / "book" / "marimo" / "notebooks"
    tests = tmp_path / "tests"
    notebooks.mkdir(parents=True)
    tests.mkdir()
    monkeypatch.setattr(check_test_layout, "ROOT", tmp_path)
    monkeypatch.setattr(check_test_layout, "NOTEBOOK_DIR", notebooks)
    monkeypatch.setattr(check_test_layout, "TESTS_DIR", tests)
    return notebooks, tests


def test_mirrored_layout_is_clean(tree):
    """A notebook with its matching test file produces no violations."""
    notebooks, tests = tree
    (notebooks / "Experiment1.py").write_text("")
    (tests / "test_experiment1.py").write_text("")

    assert check_test_layout.check() == []


def test_missing_mirror_test_is_reported(tree):
    """A notebook with no ``test_<name>.py`` is a violation."""
    notebooks, _ = tree
    (notebooks / "Experiment1.py").write_text("")

    errors = check_test_layout.check()

    assert len(errors) == 1
    assert "missing test file tests/test_experiment1.py" in errors[0]


def test_orphan_test_file_is_reported(tree):
    """A test file mapping to no notebook is a violation."""
    _, tests = tree
    (tests / "test_nothing.py").write_text("")

    errors = check_test_layout.check()

    assert len(errors) == 1
    assert "orphan test file" in errors[0]
    assert "test_nothing.py" in errors[0]


@pytest.mark.parametrize("exempt", sorted(check_test_layout._EXEMPT))
def test_exempt_test_files_are_not_orphans(tree, exempt):
    """Integration, template and script tests mirror no notebook by design."""
    _, tests = tree
    (tests / exempt).write_text("")

    assert check_test_layout.check() == []


def test_matching_is_case_insensitive(tree):
    """TitleCased notebooks map to lowercase test names."""
    notebooks, tests = tree
    (notebooks / "ExperimentFive.py").write_text("")
    (tests / "test_experimentfive.py").write_text("")

    assert check_test_layout.check() == []


def test_conftest_is_not_treated_as_a_notebook(tree):
    """``conftest.py`` beside the notebooks needs no mirror test."""
    notebooks, _ = tree
    (notebooks / "conftest.py").write_text("")

    assert check_test_layout.check() == []


def test_main_returns_zero_and_reports_success(tree, capsys):
    """Exit code 0 and a success message when the layout is clean."""
    notebooks, tests = tree
    (notebooks / "Experiment1.py").write_text("")
    (tests / "test_experiment1.py").write_text("")

    assert check_test_layout.main() == 0
    assert "Test layout OK" in capsys.readouterr().out


def test_main_returns_one_and_lists_each_violation(tree, capsys):
    """Exit code 1, printing every violation to stderr."""
    notebooks, _ = tree
    (notebooks / "Experiment1.py").write_text("")

    assert check_test_layout.main() == 1

    stderr = capsys.readouterr().err
    assert "Test-layout check failed:" in stderr
    assert "test_experiment1.py" in stderr


def test_the_real_repository_layout_is_clean():
    """The gate passes against this repository as committed.

    The tests above run on synthetic trees; this one is the guard that the real
    notebook/test layout has not drifted, independent of the pre-commit hook.
    """
    assert check_test_layout.check() == []
