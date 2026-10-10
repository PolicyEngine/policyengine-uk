"""Elasticity-based labour supply responses against the reform's baseline.

employment_income_behavioral_response, relative_wage_change and
relative_income_change compare the reform with its baseline, each measured
with labour supply responses neutralised and at the reform's earnings and gains
before responses. The baseline is ``simulation.baseline``, a separately built
simulation. These variables used to take a branch of the reform simulation
named ``baseline``, which carries the reform's parameters, so every response
was zero (issue #2268).

Each simulation below holds single-person households, one per earner. For any
earnings and elasticities:

1. With no policy change (a scenario that sets only the elasticities), the
   relative wage change, the relative income change and the response are zero.
2. A rise in the basic rate, for an earner whose £1,000 marginal-rate step
   stays inside the basic rate band, lowers the relative wage by
   (rate rise) / (1 - baseline marginal rate) and the relative income by the
   income tax rise over baseline net income. The substitution term is then
   negative and the income term positive, as positive substitution and
   negative income elasticities imply, and the response is their sum.
3. Zero elasticities give a zero response.
4. Scaling both elasticities by k scales the response by k and leaves the
   relative changes unchanged.
5. Calculating the response leaves the baseline's own results, branches and
   tax-benefit system unchanged, and keeps the response live in the reform.
6. The response does not depend on the order of calculation: calculating the
   baseline first, recalculating after deleting the response, and calculating
   periods in any order give the same values.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.scenarios.no_economic_assumptions import (
    remove_economic_assumptions,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
RESPONSE = "employment_income_behavioral_response"
WAGE_CHANGE = "relative_wage_change"
INCOME_CHANGE = "relative_income_change"
SUBSTITUTION_TERM = "substitution_elasticity_lsr"
INCOME_TERM = "income_elasticity_lsr"
BASIC_RATE = "gov.hmrc.income_tax.rates.uk[0].rate"
SUBSTITUTION_ELASTICITY = (
    "gov.simulation.labour_supply_responses.substitution_elasticity"
)
INCOME_ELASTICITY = "gov.simulation.labour_supply_responses.income_elasticity"

# 2025-26: a 20% basic rate on income above the £12,570 personal allowance,
# and 8% employee National Insurance between £12,570 and £50,270.
BASELINE_BASIC_RATE = 0.20
PERSONAL_ALLOWANCE = 12_570
EMPLOYEE_NI_RATE = 0.08
BASELINE_MARGINAL_RATE = BASELINE_BASIC_RATE + EMPLOYEE_NI_RATE

PROPERTY_SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

# Earnings whose £1,000 marginal-rate step stays above the personal allowance
# and below the higher rate threshold (£50,270).
BASIC_RATE_EARNINGS = st.integers(13_000, 49_000)
ANY_EARNINGS = st.integers(0, 200_000)
SUBSTITUTION_ELASTICITIES = st.floats(0.01, 0.5)
INCOME_ELASTICITIES = st.floats(-0.3, -0.01)


def earners(earnings, years=(YEAR,)):
    """One single-person household per earner, aged 30 throughout."""
    people = {
        f"earner_{i}": {
            "age": {year: 30 for year in years},
            "employment_income": {years[0]: amount},
        }
        for i, amount in enumerate(earnings)
    }
    return {
        "people": people,
        "benunits": {f"{name}_benunit": {"members": [name]} for name in people},
        "households": {f"{name}_household": {"members": [name]} for name in people},
    }


def changes(substitution, income, basic_rate=None, years=(YEAR,)):
    parameter_changes = {
        SUBSTITUTION_ELASTICITY: {str(year): substitution for year in years},
        INCOME_ELASTICITY: {str(year): income for year in years},
    }
    if basic_rate is not None:
        parameter_changes[BASIC_RATE] = {str(year): basic_rate for year in years}
    return parameter_changes


def simulate(earnings, substitution, income, basic_rate=None, years=(YEAR,)):
    return Simulation(
        situation=earners(earnings, years),
        scenario=Scenario(
            parameter_changes=changes(substitution, income, basic_rate, years)
        ),
    )


def values(simulation, variable, period=YEAR):
    return np.asarray(simulation.calculate(variable, period), dtype=float)


def response_parts(simulation, period=YEAR):
    """The response first, as the relative changes require."""
    return {
        variable: values(simulation, variable, period)
        for variable in (
            RESPONSE,
            WAGE_CHANGE,
            INCOME_CHANGE,
            SUBSTITUTION_TERM,
            INCOME_TERM,
        )
    }


def test_reform_raising_the_basic_rate_responds_by_hand_calculated_amounts():
    """The case in issue #2268, checked by hand.

    £40,000 of earnings in 2025-26. Baseline income tax is 20% of £27,430
    (£40,000 less the £12,570 personal allowance), £5,486; at a 30% basic
    rate it is £8,229, £2,743 more. Baseline net income is £40,000 less that
    tax, employee NI of 8% of £27,430 (£2,194.40), the £174.50 TV licence and
    the model's £0.045 of expected stamp duty: £32,145.055.

    The marginal rate rises from 28% to 38%, so the wage after tax falls from
    0.72 to 0.62 of pay: a relative change of -0.10 / 0.72 = -5/36. Net
    income falls by 2,743 / 32,145.055. With elasticities of 0.25 and -0.05
    the response is 40,000 x (0.25 x -5/36 + -0.05 x -2,743 / 32,145.055)
    = -1,388.89 + 170.66 = -£1,218.23.
    """
    sim = simulate([40_000], substitution=0.25, income=-0.05, basic_rate=0.30)
    parts = response_parts(sim)

    wage_change = -0.10 / 0.72
    income_change = -2_743 / 32_145.055
    substitution_term = 40_000 * 0.25 * wage_change
    income_term = 40_000 * -0.05 * income_change

    assert parts[WAGE_CHANGE] == pytest.approx([wage_change], rel=1e-5)
    assert parts[INCOME_CHANGE] == pytest.approx([income_change], rel=1e-5)
    assert parts[SUBSTITUTION_TERM] == pytest.approx([-1_388.889], abs=0.01)
    assert parts[INCOME_TERM] == pytest.approx([170.664], abs=0.01)
    assert parts[RESPONSE] == pytest.approx([substitution_term + income_term], abs=0.01)
    assert parts[RESPONSE] == pytest.approx([-1_218.225], abs=0.01)
    # The response reaches employment income, and through it income tax.
    earnings = 40_000 + parts[RESPONSE][0]
    assert values(sim, "employment_income") == pytest.approx([earnings], abs=0.01)
    assert values(sim, "income_tax") == pytest.approx(
        [0.30 * (earnings - PERSONAL_ALLOWANCE)], abs=0.01
    )
    # The baseline keeps its tax.
    assert values(sim.baseline, "income_tax") == pytest.approx([5_486])


@PROPERTY_SETTINGS
@given(
    earnings=st.lists(ANY_EARNINGS, min_size=1, max_size=4),
    substitution=SUBSTITUTION_ELASTICITIES,
    income=INCOME_ELASTICITIES,
)
def test_no_policy_change_gives_no_response(earnings, substitution, income):
    """Invariant 1: elasticities alone change nothing to respond to."""
    parts = response_parts(simulate(earnings, substitution, income))

    for variable, array in parts.items():
        np.testing.assert_array_equal(array, 0, err_msg=variable)


def test_simulation_without_a_scenario_gives_no_response():
    """Invariant 1 where the baseline is the simulation's own clone.

    A simulation built without a scenario keeps a clone of itself as its
    baseline. Setting the elasticities on it afterwards changes no policy the
    baseline measures differently.
    """
    sim = Simulation(situation=earners([20_000, 40_000, 80_000]))
    sim.apply_parameter_changes(changes(0.25, -0.05))

    parts = response_parts(sim)

    assert (
        sim.tax_benefit_system.parameters(
            str(YEAR)
        ).gov.simulation.labour_supply_responses.substitution_elasticity
        == 0.25
    )
    for variable, array in parts.items():
        np.testing.assert_array_equal(array, 0, err_msg=variable)


@PROPERTY_SETTINGS
@given(
    earnings=st.lists(BASIC_RATE_EARNINGS, min_size=1, max_size=4),
    basic_rate=st.sampled_from([0.22, 0.25, 0.30, 0.40]),
    substitution=SUBSTITUTION_ELASTICITIES,
    income=INCOME_ELASTICITIES,
)
def test_basic_rate_rise_gives_responses_of_the_implied_sign(
    earnings, basic_rate, substitution, income
):
    """Invariant 2: a basic rate rise lowers the wage and income after tax."""
    sim = simulate(earnings, substitution, income, basic_rate)
    parts = response_parts(sim)
    earnings = np.array(earnings, dtype=float)

    rise = basic_rate - BASELINE_BASIC_RATE
    expected_wage_change = -rise / (1 - BASELINE_MARGINAL_RATE)
    np.testing.assert_allclose(parts[WAGE_CHANGE], expected_wage_change, rtol=1e-4)
    baseline_net_income = values(sim.baseline, "household_net_income")
    tax_rise = rise * (earnings - PERSONAL_ALLOWANCE)
    np.testing.assert_allclose(
        parts[INCOME_CHANGE], -tax_rise / baseline_net_income, rtol=1e-4
    )

    assert (parts[SUBSTITUTION_TERM] < 0).all()
    assert (parts[INCOME_TERM] > 0).all()
    np.testing.assert_allclose(
        parts[SUBSTITUTION_TERM],
        earnings * substitution * parts[WAGE_CHANGE],
        rtol=1e-5,
    )
    np.testing.assert_allclose(
        parts[INCOME_TERM], earnings * income * parts[INCOME_CHANGE], rtol=1e-5
    )
    np.testing.assert_allclose(
        parts[RESPONSE],
        parts[SUBSTITUTION_TERM] + parts[INCOME_TERM],
        rtol=1e-5,
        atol=0.01,
    )


@PROPERTY_SETTINGS
@given(
    earnings=st.lists(ANY_EARNINGS, min_size=1, max_size=4),
    basic_rate=st.sampled_from([0.15, 0.25, 0.30]),
)
def test_zero_elasticities_give_no_response(earnings, basic_rate):
    """Invariant 3."""
    sim = simulate(earnings, 0, 0, basic_rate)

    np.testing.assert_array_equal(values(sim, RESPONSE), 0)
    np.testing.assert_allclose(values(sim, "employment_income"), earnings, rtol=1e-6)


# Each example builds two reforms, each with its baseline.
@settings(PROPERTY_SETTINGS, max_examples=4)
@given(
    earnings=st.lists(ANY_EARNINGS, min_size=1, max_size=4),
    basic_rate=st.sampled_from([0.15, 0.25, 0.30]),
    substitution=SUBSTITUTION_ELASTICITIES,
    income=INCOME_ELASTICITIES,
    factor=st.sampled_from([0.5, 2.0, 3.0]),
)
def test_response_scales_with_the_elasticities(
    earnings, basic_rate, substitution, income, factor
):
    """Invariant 4: the relative changes do not depend on the elasticities."""
    base = response_parts(simulate(earnings, substitution, income, basic_rate))
    scaled = response_parts(
        simulate(earnings, factor * substitution, factor * income, basic_rate)
    )

    np.testing.assert_array_equal(scaled[WAGE_CHANGE], base[WAGE_CHANGE])
    np.testing.assert_array_equal(scaled[INCOME_CHANGE], base[INCOME_CHANGE])
    # The response is stored as float32.
    np.testing.assert_allclose(
        scaled[RESPONSE], factor * base[RESPONSE], rtol=1e-5, atol=0.01
    )


def test_response_leaves_the_baseline_unchanged():
    """Invariant 5."""
    sim = simulate([18_000, 40_000, 75_000], 0.25, -0.05, basic_rate=0.30)
    baseline = sim.baseline
    measured = (
        "household_net_income",
        "income_tax",
        "marginal_tax_rate",
        "employment_income",
        RESPONSE,
    )
    before = {variable: values(baseline, variable) for variable in measured}
    branches = set(baseline.branches)
    baseline_response = baseline.tax_benefit_system.variables[RESPONSE]
    reform_response = sim.tax_benefit_system.variables[RESPONSE]

    response = values(sim, RESPONSE)
    # Basic rate taxpayers face a higher marginal rate and lower income, and
    # work less. The higher rate taxpayer's marginal rate is unchanged, so
    # only the fall in income acts, and with a negative income elasticity
    # they work more.
    assert (response[:2] < 0).all()
    assert response[2] > 0

    for variable in measured:
        np.testing.assert_array_equal(
            values(baseline, variable), before[variable], err_msg=variable
        )
    assert set(baseline.branches) == branches
    assert baseline.tax_benefit_system.variables[RESPONSE] is baseline_response
    assert sim.tax_benefit_system.variables[RESPONSE] is reform_response
    assert not reform_response.is_neutralized
    # The measurement branches are not kept.
    assert "lsr_measurement" not in sim.branches
    assert "baseline_lsr_measurement" not in baseline.branches


def remove_growth_and_raise_the_basic_rate(simulation):
    remove_economic_assumptions(simulation)
    parameters = simulation.tax_benefit_system.parameters
    for name, value in (
        (SUBSTITUTION_ELASTICITY, 0.25),
        (INCOME_ELASTICITY, -0.05),
        (BASIC_RATE, 0.30),
    ):
        parameters.get_child(name).update(period="year:2000:100", value=value)
    simulation.tax_benefit_system.reset_parameter_caches()


def test_response_does_not_depend_on_calculating_the_baseline_first():
    """Invariant 6, where the reform's data differ from the baseline's.

    Without economic assumptions the reform's 2026 earnings stay at their
    2025 level, while the baseline's grow. A measurement branch of the
    baseline started from what the baseline had calculated at its own
    earnings, and read those results in place of results at the reform's: the
    response was -1,218.20 calculated alone and -1,164.16 with the baseline
    calculated first.
    """

    def build():
        return Simulation(
            situation=earners([40_000], years=(2025, 2026)),
            scenario=Scenario(
                simulation_modifier=remove_growth_and_raise_the_basic_rate,
                applied_before_data_load=True,
            ),
        )

    alone = build()
    assert values(alone, "employment_income_before_lsr", 2026) == pytest.approx(
        [40_000]
    )
    assert values(alone.baseline, "employment_income_before_lsr", 2026)[0] > 40_000
    expected = response_parts(alone, 2026)

    baseline_first = build()
    values(baseline_first.baseline, "household_net_income", 2026)
    values(baseline_first.baseline, "marginal_tax_rate", 2026)
    parts = response_parts(baseline_first, 2026)

    assert expected[RESPONSE][0] < 0
    for variable, array in expected.items():
        np.testing.assert_array_equal(parts[variable], array, err_msg=variable)


def test_recalculation_gives_the_same_response():
    """Invariant 6 on recalculation.

    The reform's measurement branch started from what the reform had
    calculated, including household net income after the response, so
    deleting the response and calculating it again gave -1,171.23 instead of
    -1,218.23.
    """
    sim = simulate([40_000], 0.25, -0.05, basic_rate=0.30)
    values(sim, "household_net_income")
    first = response_parts(sim)
    for variable in first:
        sim.delete_arrays(variable, YEAR)
    second = response_parts(sim)
    sim.reset_calculations()
    third = response_parts(sim)

    for variable, array in first.items():
        np.testing.assert_array_equal(second[variable], array, err_msg=variable)
        np.testing.assert_array_equal(third[variable], array, err_msg=variable)


def test_periods_give_the_same_response_in_any_order():
    """Invariant 6 across periods, against one period per simulation."""
    years = (2025, 2026, 2027)

    def build():
        return simulate([25_000, 40_000], 0.25, -0.05, basic_rate=0.30, years=years)

    alone = {year: values(build(), RESPONSE, year) for year in years}
    forwards, backwards = build(), build()
    in_order = {year: values(forwards, RESPONSE, year) for year in years}
    reversed_order = {
        year: values(backwards, RESPONSE, year) for year in reversed(years)
    }

    for year in years:
        assert (alone[year] < 0).all()
        np.testing.assert_array_equal(in_order[year], alone[year])
        np.testing.assert_array_equal(reversed_order[year], alone[year])
