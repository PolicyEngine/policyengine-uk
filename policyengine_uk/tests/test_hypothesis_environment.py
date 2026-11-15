"""Hypothesis draws the same examples from the source tree and the wheel.

conftest.py stops Hypothesis drawing literal constants from local modules,
which it collects from the source tree but not from an installed wheel
(issue #2397). This fails if a Hypothesis upgrade bypasses that.
"""

from hypothesis.internal.conjecture import providers

# Imported so its modules are loaded, as in any test that uses the model: in
# a source checkout they are local modules with many literal constants.
import policyengine_uk  # noqa: F401


def test_hypothesis_draws_no_constants_from_local_modules():
    # Read the pool the way Hypothesis's own provider does.
    local_constants = providers.HypothesisProvider(None)._local_constants
    assert len(local_constants) == 0
