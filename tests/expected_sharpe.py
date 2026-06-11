"""Pinned Sharpe-ratio baselines, shared across the test suite.

These values are the single source of truth for what each experiment notebook
(run with its default slider parameters) is expected to produce. They are used
both by ``test_notebook_sharpe.py`` (executes the notebooks end-to-end) and by
``test_optimize.py`` (checks that the ``build_exp*`` builders in
``optimize.py`` reproduce the notebooks numerically).

The tight 1e-6 tolerances are deliberate: any change to the strategy logic or
to a dependency that perturbs floating point should fail loudly. See
``docs/development/SHARPE_PINS.md`` for how to review and update the pins.
"""

EXPECTED_SHARPE_RATIOS = {
    "Experiment1": 0.5605552118857117,
    "Experiment2": 0.8793799321235558,
    "Experiment3": 0.8776423555933839,
    "Experiment4": 1.0712152818814276,
    "Experiment5": 1.4652366037605955,
}

SHARPE_RATIO_REL_TOLERANCE = 1e-6
SHARPE_RATIO_ABS_TOLERANCE = 1e-6
