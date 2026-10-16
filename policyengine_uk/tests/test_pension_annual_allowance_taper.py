"""MOCK population tests for the FA 2004 s. 228ZA annual allowance taper.

The historical values come from Finance (No. 2) Act 2015 Sch. 4 para. 10,
Finance Act 2020 s. 22 and Finance (No. 2) Act 2023 ss. 20 and 22. The
threshold-income limit is the adjusted-income limit less the standard annual
allowance (s. 228ZA(3)(b)). All simulations use synthetic situations.

Invariants: the allowance stays between the statutory minimum and standard
amount; it stays at the standard amount unless both gates are exceeded; and
above the threshold-income gate it never rises with adjusted income. Every
reduction is a whole number of pounds (s. 228ZA(2)).
"""

import math

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation


# (adjusted-income limit, threshold-income limit, minimum, standard allowance).
# These expected values are statutory fixtures, independent of model parameters.
PERIODS = {
    **{year: (150_000, 110_000, 10_000, 40_000) for year in range(2016, 2020)},
    **{year: (240_000, 200_000, 4_000, 40_000) for year in range(2020, 2023)},
    **{year: (260_000, 200_000, 10_000, 60_000) for year in range(2023, 2028)},
}
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
income_pair = st.tuples(st.integers(0, 1_000_000), st.integers(0, 500_000))
population = st.lists(income_pair, min_size=4, max_size=10)


def _simulation(incomes, year):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for index, (adjusted, threshold) in enumerate(incomes):
        name = f"p{index}"
        situation["people"][name] = {
            "age": {year: 45},
            "pension_annual_allowance_adjusted_income": {year: adjusted},
            "pension_annual_allowance_threshold_income": {year: threshold},
        }
        situation["benunits"][f"b{index}"] = {"members": [name]}
        situation["households"][f"h{index}"] = {"members": [name]}
    return Simulation(situation=situation)


@pytest.mark.parametrize("year,expected", PERIODS.items())
def test_historical_taper_parameters(year, expected):
    """Cover every tax year at both sides of each legislative change."""
    sim = _simulation([(0, 0)], year)
    parameters = sim.tax_benefit_system.parameters(
        year
    ).gov.hmrc.income_tax.allowances.annual_allowance
    adjusted, threshold, minimum, standard = expected
    assert float(parameters.taper) == adjusted
    assert float(parameters.default) == standard
    assert float(parameters.taper - parameters.default) == threshold
    assert float(parameters.minimum) == minimum
    assert float(parameters.reduction_rate) == 0.5


@PROPERTY_SETTINGS
@given(population, st.sampled_from(list(PERIODS)))
def test_allowance_bounds_and_statutory_two_gate_reference(incomes, year):
    adjusted_limit, threshold_limit, minimum, standard = PERIODS[year]
    sim = _simulation(incomes, year)
    allowance = np.asarray(sim.calculate("pension_annual_allowance", year))
    assert np.all(allowance >= minimum)
    assert np.all(allowance <= standard)
    assert np.all(allowance == np.floor(allowance))

    expected = []
    for adjusted, threshold in incomes:
        if adjusted <= adjusted_limit or threshold <= threshold_limit:
            expected.append(standard)
        else:
            reduction = math.floor((adjusted - adjusted_limit) / 2)
            expected.append(max(minimum, standard - reduction))
    np.testing.assert_array_equal(allowance, expected)


@PROPERTY_SETTINGS
@given(
    st.lists(st.integers(1, 1_000_000), min_size=4, max_size=12),
    st.integers(1, 200_000),
    st.sampled_from(list(PERIODS)),
)
def test_allowance_is_nonincreasing_in_adjusted_income_above_gate(
    excesses, threshold_excess, year
):
    adjusted_limit, threshold_limit, minimum, standard = PERIODS[year]
    # Include the untapered boundary and a fully tapered endpoint so a
    # constant output cannot satisfy the property merely by ignoring inputs.
    adjusted_incomes = [adjusted_limit] + sorted(
        adjusted_limit + excess for excess in excesses
    )
    adjusted_incomes.append(adjusted_limit + 2 * (standard - minimum))
    adjusted_incomes.sort()
    sim = _simulation(
        [
            (adjusted, threshold_limit + threshold_excess)
            for adjusted in adjusted_incomes
        ],
        year,
    )
    allowance = np.asarray(sim.calculate("pension_annual_allowance", year))
    assert np.all(np.diff(allowance) <= 0)
    assert allowance[0] == standard
    assert allowance[-1] == minimum


@PROPERTY_SETTINGS
@given(population, st.sampled_from(list(PERIODS)))
def test_threshold_income_gate_preserves_standard_allowance(incomes, year):
    adjusted_limit, threshold_limit, _, standard = PERIODS[year]
    # Vary adjusted income above its limit while threshold income is at or
    # below its own limit, including equality for every generated population.
    cases = [(adjusted_limit + 100_000, threshold_limit)] + [
        (adjusted_limit + adjusted + 1, min(threshold, threshold_limit))
        for adjusted, threshold in incomes
    ]
    sim = _simulation(cases, year)
    allowance = np.asarray(sim.calculate("pension_annual_allowance", year))
    np.testing.assert_array_equal(allowance, np.full(len(cases), standard))


def test_pre_2020_allowance_reform_changes_multiplier_and_threshold_gate():
    """Original s. 228ZA uses (standard minus minimum) / 60,000."""
    year = 2018
    sim = _simulation([(156_000, 130_001), (156_000, 130_000)], year)
    sim.apply_parameter_changes(
        {"gov.hmrc.income_tax.allowances.annual_allowance.default": {"2018": 20_000}}
    )
    allowance = sim.calculate("pension_annual_allowance", year)
    # Gate = 150,000 - 20,000. Reduction = 6,000 * 10,000 / 60,000.
    np.testing.assert_array_equal(allowance, [19_000, 20_000])


def test_post_2020_allowance_reform_keeps_half_rate_and_changes_threshold_gate():
    """FA 2020 s. 22 fixes the multiplier at one half after 2019-20."""
    year = 2024
    sim = _simulation([(280_000, 220_001), (280_000, 220_000)], year)
    sim.apply_parameter_changes(
        {"gov.hmrc.income_tax.allowances.annual_allowance.default": {"2024": 40_000}}
    )
    allowance = sim.calculate("pension_annual_allowance", year)
    # Gate = 260,000 - 40,000. Reduction = (280,000 - 260,000) / 2.
    np.testing.assert_array_equal(allowance, [30_000, 40_000])
