"""Savings nil-rate position and disjoint band allocation under reforms.

ITA 2007 ss.12,12A,12B and16 fix the income ordering and nil slice.
These unit-level inputs exercise the banding contract independently of
personal-allowance/PSA selection, which the natural YAML cases keep live.
Custom phase-out values preserve the existing model reform contract.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_core.reforms import Reform
from policyengine_core.simulations import SimulationBuilder

from policyengine_uk import CountryTaxBenefitSystem

YEAR = 2026
PEOPLE = 6
BASIC_LIMIT = 37_700
HIGHER_LIMIT = 125_140
BANDS = (
    "basic_rate_savings_income",
    "higher_rate_savings_income",
    "add_rate_savings_income",
)
row = st.tuples(
    st.integers(min_value=0, max_value=130_000),
    st.integers(min_value=0, max_value=500),
    st.sampled_from([0, 500, 1_000]),
)
rows = st.lists(row, min_size=PEOPLE, max_size=PEOPLE)


def _reference(non_savings, savings, allowance, limit, phase_out):
    """Classify each pound once, rather than subtract overlapping reliefs."""
    starter = min(
        savings,
        max(0, BASIC_LIMIT - non_savings),
        max(0, limit - non_savings * phase_out),
    )
    nil_start = max(non_savings, limit)
    charged = [0, 0, 0]
    zero = 0
    for pound in range(savings):
        position = non_savings + pound + 0.5
        if (
            position < non_savings + starter
            or nil_start <= position < nil_start + allowance
        ):
            zero += 1
        elif position < BASIC_LIMIT:
            charged[0] += 1
        elif position < HIGHER_LIMIT:
            charged[1] += 1
        else:
            charged[2] += 1
    assert zero + sum(charged) == savings
    return charged, zero


@pytest.fixture(scope="module")
def savings_tax_benefit_system():
    return CountryTaxBenefitSystem()


def _calculated(rows, limit, phase_out, baseline):
    people, benunits, households = {}, {}, {}
    for i, (non_savings, savings, allowance) in enumerate(rows):
        name = f"p{i}"
        people[name] = {
            "age": {YEAR: 40},
            "non_savings_taxable_income": {YEAR: non_savings},
            "taxable_savings_interest_income": {YEAR: savings},
            "received_allowances_savings_income": {YEAR: 0},
            "savings_allowance": {YEAR: allowance},
        }
        benunits[f"b{i}"] = {"members": [name]}
        households[f"h{i}"] = {"members": [name], "region": {YEAR: "LONDON"}}
    reform = Reform.from_dict(
        {
            "gov.hmrc.income_tax.rates.savings_starter_rate.allowance": {
                str(YEAR): limit
            },
            "gov.hmrc.income_tax.rates.savings_starter_rate.phase_out": {
                str(YEAR): phase_out
            },
        }
    )
    system = reform(baseline.clone())
    builder = SimulationBuilder()
    builder.set_default_period(YEAR)
    simulation = builder.build_from_dict(
        system, {"people": people, "benunits": benunits, "households": households}
    )
    simulation.default_calculation_period = builder.default_period
    bands = np.stack(
        [np.asarray(simulation.calculate(band, YEAR)).copy() for band in BANDS],
        axis=1,
    )
    tax = np.asarray(simulation.calculate("savings_income_tax", YEAR)).copy()
    return bands, tax


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    rows=rows,
    limit=st.integers(min_value=0, max_value=140_000),
    phase_out=st.sampled_from([0, 1, 2]),
)
@example(rows=[(37_500, 500, 500)] * PEOPLE, limit=37_500, phase_out=1)
@example(rows=[(37_500, 500, 500)] * PEOPLE, limit=40_000, phase_out=1)
@example(rows=[(3_000, 6_000, 1_000)] * PEOPLE, limit=5_000, phase_out=0)
def test_savings_bands_equal_disjoint_statutory_slices(
    savings_tax_benefit_system, rows, limit, phase_out
):
    expected = [_reference(*row, limit, phase_out) for row in rows]
    expected_bands = np.asarray([charged for charged, _ in expected])
    expected_zero = np.asarray([zero for _, zero in expected])
    actual_bands, actual_tax = _calculated(
        rows, limit, phase_out, savings_tax_benefit_system
    )
    assert np.all(actual_bands >= 0)
    np.testing.assert_array_equal(actual_bands, expected_bands)
    np.testing.assert_array_equal(
        actual_bands.sum(axis=1) + expected_zero,
        [savings for _, savings, _ in rows],
    )
    np.testing.assert_allclose(
        actual_tax, expected_bands @ np.asarray([0.2, 0.4, 0.45]), atol=0.01
    )
