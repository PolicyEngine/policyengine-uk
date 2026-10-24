"""Properties of VAT grossing that hold for every input (#2633).

`vat` is the statutory liability on recorded consumption divided by one
grossing factor. The factor is the survey coverage times the household share
of receipts, unless a reform moves the deprecated combined parameter, in which
case that value is used.
"""

from types import SimpleNamespace

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.vat import LEGACY_COVERAGE_DEFAULT, vat_grossing_factor

SHARE = st.floats(min_value=0.01, max_value=1, allow_nan=False)
SPEND = st.floats(min_value=0, max_value=1e6, allow_nan=False)
# A legacy value counts as untouched when it is within NumPy's default
# closeness of the declared default: 1e-8 plus 1e-5 times the default.
BAND = 1e-8 + 1e-5 * abs(LEGACY_COVERAGE_DEFAULT)


def params(legacy, coverage, share):
    return SimpleNamespace(
        microdata_vat_coverage=legacy,
        vat=SimpleNamespace(
            survey_consumption_coverage=coverage,
            household_share_of_receipts=share,
        ),
    )


# The helper properties check algebra and routing, not speed, so they have no
# deadline: a slow first example on a loaded host is not a failure.
@settings(deadline=None)
@given(coverage=SHARE, share=SHARE)
def test_untouched_legacy_factor_uses_the_product_of_the_two(coverage, share):
    factor = vat_grossing_factor(params(LEGACY_COVERAGE_DEFAULT, coverage, share))
    assert factor == pytest.approx(coverage * share)


@settings(deadline=None)
@given(
    offset=st.floats(min_value=-0.99, max_value=0.99),
    coverage=SHARE,
    share=SHARE,
)
def test_legacy_factor_within_the_band_counts_as_untouched(offset, coverage, share):
    legacy = LEGACY_COVERAGE_DEFAULT + offset * BAND
    factor = vat_grossing_factor(params(legacy, coverage, share))
    assert factor == pytest.approx(coverage * share)


@settings(deadline=None)
@given(legacy=SHARE, coverage=SHARE, share=SHARE)
def test_moved_legacy_factor_overrides_the_two(legacy, coverage, share):
    assume(abs(legacy - LEGACY_COVERAGE_DEFAULT) > 1.01 * BAND)
    factor = vat_grossing_factor(params(legacy, coverage, share))
    assert factor == legacy


@pytest.mark.parametrize(
    "multiple, moved", [(-1.01, True), (-0.99, False), (0.99, False), (1.01, True)]
)
def test_legacy_factor_either_side_of_the_band(multiple, moved):
    legacy = LEGACY_COVERAGE_DEFAULT + multiple * BAND
    factor = vat_grossing_factor(params(legacy, 0.5, 0.7))
    assert factor == (legacy if moved else pytest.approx(0.35))


@settings(max_examples=5, deadline=None)
@given(spend=st.lists(st.tuples(SPEND, SPEND), min_size=1, max_size=20))
def test_vat_is_statutory_liability_over_the_shipped_product(spend):
    # One simulation of many households, so the property is checked on a
    # vector: VAT is linear in each household's recorded consumption, with
    # no cross-household term.
    p = system.parameters.gov
    product = p.simulation.vat.survey_consumption_coverage(
        2025
    ) * p.simulation.vat.household_share_of_receipts(2025)
    names = [f"h{i}" for i in range(len(spend))]
    situation = {
        "people": {f"p{i}": {"age": {2025: 40}} for i in range(len(spend))},
        "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(len(spend))},
        "households": {
            name: {
                "members": [f"p{i}"],
                "full_rate_vat_consumption": {2025: full},
                "reduced_rate_vat_consumption": {2025: reduced},
            }
            for i, (name, (full, reduced)) in enumerate(zip(names, spend))
        },
    }
    vat = Simulation(situation=situation).calculate("vat", 2025)
    for value, (full, reduced) in zip(vat, spend):
        expected = (
            full * p.hmrc.vat.standard_rate(2025)
            + reduced * p.hmrc.vat.reduced_rate(2025)
        ) / product
        assert value == pytest.approx(expected, rel=1e-5, abs=1e-2)
