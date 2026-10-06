"""Tests for calculate_dependency_contributions in policyengine_uk.utils.dependencies.

The contribution of a variable the target reads directly (a direct dependency)
is the mean of the target minus the mean of the target recalculated with that
dependency zero in the year and every other value as already calculated. For
any household drawn below:

1. Matches a reference: each float dependency's contribution equals the one
   from a fresh simulation in which the target's float direct dependencies are
   inputs at their calculated values, except the zeroed one. The reference
   uses no branches and deletes nothing.
2. Adds up: for a target defined only by `adds` and `subtracts` of its direct
   dependencies, the contributions sum to the mean of the target.
3. Leaves the simulation as it was: every value it stored before the call is
   stored, unchanged, after it, and nothing is added (no values, no recorded
   inputs, no branches). So a second call returns the same contributions.
4. Non-float dependencies contribute zero.

Monthly variables are the case that broke: zeroing a monthly dependency over a
year, or restoring it, raised "Inconsistent input", because the months already
held values that did not add up to the annual one. Comparisons allow float32
rounding: the model stores values as float32.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from plotly import graph_objects as go

from policyengine_core import periods
from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.utils.dependencies import (
    calculate_dependency_contribution_change,
    calculate_dependency_contributions,
    create_waterfall_chart,
    get_variable_dependencies,
)

YEARS = [2024, 2025, 2026, 2027]
# Defined only by adds and subtracts of their direct dependencies.
ADDITIVE_TARGETS = [
    "household_net_income",
    "ni_employee",
    "ni_class_1_employee",
    "child_benefit_entitlement",
]
TARGETS = ADDITIVE_TARGETS + ["child_benefit", "income_tax"]
# A target and a monthly float variable it reads directly.
MONTHLY_DEPENDENCIES = [
    ("ni_employee", "ni_class_1_employee"),
    ("child_benefit_entitlement", "child_benefit_respective_amount"),
    # A monthly target: its direct dependencies are what its months read.
    ("ni_class_1_employee", "ni_class_1_employee_primary"),
    ("ni_class_1_employee", "ni_class_1_employee_additional"),
]
NI_MAIN_RATE = "gov.hmrc.national_insurance.class_1.rates.employee.main"
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def tolerance(*amounts):
    return 0.01 + 1e-6 * max([abs(float(a)) for a in amounts] + [0])


def make_situation(year, adults, child_ages):
    people = {}
    for i, (age, earnings) in enumerate(adults):
        people[f"adult_{i}"] = {
            "age": {year: age},
            "employment_income": {year: earnings},
        }
    for i, age in enumerate(child_ages):
        people[f"child_{i}"] = {"age": {year: age}}
    members = list(people)
    return {
        "people": people,
        "benunits": {"benunit": {"members": members}},
        "households": {"household": {"members": members}},
    }


# Earnings above the upper earnings limit, and a child: every monthly
# dependency above is non-zero.
EARNER_WITH_CHILD = (2026, [(40, 80_000.0)], [3])


@st.composite
def households(draw):
    earnings = st.one_of(
        st.just(0.0),
        st.floats(0, 250_000, allow_nan=False, allow_infinity=False),
        st.integers(0, 250_000).map(float),
    )
    year = draw(st.sampled_from(YEARS))
    adults = draw(
        st.lists(st.tuples(st.integers(18, 90), earnings), min_size=1, max_size=2)
    )
    child_ages = draw(st.lists(st.integers(0, 17), max_size=3))
    return year, adults, child_ages


def traced_simulation(year, adults, child_ages, targets=TARGETS):
    sim = Simulation(situation=make_situation(year, adults, child_ages), trace=True)
    for target in targets:
        sim.calculate(target, year)
    return sim


def float_dependencies(sim, target):
    return [
        dependency
        for dependency in dict.fromkeys(get_variable_dependencies(target, sim))
        if sim.tax_benefit_system.get_variable(dependency).value_type == float
    ]


def definition_periods(sim, variable, year):
    variable = sim.tax_benefit_system.get_variable(variable)
    return periods.period(year).get_subperiods(variable.definition_period)


def stored_values(sim):
    values = {}
    for name in sim.tax_benefit_system.variables:
        holder = sim.get_holder(name)
        for branch_name, period in holder.get_known_branch_periods():
            values[name, branch_name, str(period)] = np.array(
                holder.get_array(period, branch_name)
            )
    return values


def recorded_inputs(sim):
    # The record of set_input values that apply_reform keeps and
    # to_input_dataframe exports, for the names sim reads.
    visible = {"default", sim.branch_name}
    return {key for key in getattr(sim, "_user_input_keys", set()) if key[1] in visible}


def assert_unchanged(sim, before):
    values, inputs, branches = before
    after = stored_values(sim)
    assert after.keys() == values.keys()
    for key, array in values.items():
        assert np.array_equal(after[key], array), key
    assert recorded_inputs(sim) == inputs
    assert set(sim.branches) == branches


def snapshot(sim):
    return stored_values(sim), recorded_inputs(sim), set(sim.branches)


def reference_contributions(year, adults, child_ages, target, dependencies, values):
    base = Simulation(situation=make_situation(year, adults, child_ages))

    def recalculate(zeroed=None):
        sim = base.clone(clone_tax_benefit_system=False)
        for dependency in dependencies:
            for period, array in values[dependency].items():
                if dependency == zeroed:
                    array = np.zeros_like(array)
                sim.set_input(dependency, period, array)
        return sim.calculate(target, year)

    original = recalculate()
    return original, {
        dependency: (original - recalculate(dependency)).mean()
        for dependency in dependencies
    }


@pytest.mark.parametrize("target,dependency", MONTHLY_DEPENDENCIES)
def test_monthly_dependency_contributes_its_value(target, dependency):
    year, adults, child_ages = EARNER_WITH_CHILD
    sim = traced_simulation(year, adults, child_ages, [target])
    # Each of these targets adds its monthly dependencies, so zeroing one
    # removes exactly its annual total, summed to the target's entity.
    entity = sim.tax_benefit_system.get_variable(target).entity.key
    expected = sim.calculate(dependency, year, map_to=entity).mean()
    assert expected > 0

    contributions = calculate_dependency_contributions(sim, target, year)

    assert contributions[dependency] == pytest.approx(expected, abs=tolerance(expected))


def test_monthly_target_reads_its_months_dependencies():
    year, adults, child_ages = EARNER_WITH_CHILD
    sim = traced_simulation(year, adults, child_ages, ["ni_class_1_employee"])

    dependencies = set(get_variable_dependencies("ni_class_1_employee", sim))

    assert dependencies == {
        "ni_liable",
        "ni_class_1_employee_primary",
        "ni_class_1_employee_additional",
    }


def test_dependency_that_matters_contributes():
    year, adults, child_ages = EARNER_WITH_CHILD
    sim = traced_simulation(year, adults, child_ages, ["household_net_income"])

    contributions = calculate_dependency_contributions(
        sim, "household_net_income", year
    )

    for dependency, sign in [
        ("household_market_income", 1),
        ("household_benefits", 1),
        ("household_tax", -1),
    ]:
        expected = sign * sim.calculate(dependency, year).mean()
        assert expected != 0
        assert contributions[dependency] == pytest.approx(
            expected, abs=tolerance(expected)
        )


def test_additive_targets_are_sums():
    system = Simulation(
        situation=make_situation(2026, [(40, 0.0)], [])
    ).tax_benefit_system
    for target in ADDITIVE_TARGETS:
        variable = system.get_variable(target)
        assert not variable.formulas, target
        assert variable.adds or variable.subtracts, target


@PROPERTY_SETTINGS
@given(households())
@example(EARNER_WITH_CHILD)
def test_contributions_add_up_and_leave_the_simulation_unchanged(household):
    year, adults, child_ages = household
    sim = traced_simulation(year, adults, child_ages)
    before = snapshot(sim)

    for target in TARGETS:
        contributions = calculate_dependency_contributions(sim, target, year)
        assert_unchanged(sim, before)
        pd.testing.assert_series_equal(
            calculate_dependency_contributions(sim, target, year), contributions
        )

        floats = float_dependencies(sim, target)
        assert set(contributions.index) == {
            dependency
            for dependency in get_variable_dependencies(target, sim)
            if "weight" not in dependency
        }
        for dependency in contributions.index.difference(floats):
            assert contributions[dependency] == 0, (target, dependency)

        if target in ADDITIVE_TARGETS:
            mean = sim.calculate(target, year).mean()
            assert contributions.sum() == pytest.approx(
                mean, abs=tolerance(mean, *contributions)
            ), target


@settings(PROPERTY_SETTINGS, max_examples=5)
@given(households(), st.sampled_from(TARGETS))
@example(EARNER_WITH_CHILD, "ni_class_1_employee")
@example(EARNER_WITH_CHILD, "child_benefit_entitlement")
def test_contributions_match_a_reference_without_branches(household, target):
    year, adults, child_ages = household
    sim = traced_simulation(year, adults, child_ages, [target])
    dependencies = float_dependencies(sim, target)
    values = {
        dependency: {
            period: sim.calculate(dependency, period)
            for period in definition_periods(sim, dependency, year)
        }
        for dependency in dependencies
    }

    contributions = calculate_dependency_contributions(sim, target, year)
    original, expected = reference_contributions(
        year, adults, child_ages, target, dependencies, values
    )

    target_values = sim.calculate(target, year)
    assert np.allclose(original, target_values, atol=0.01)
    for dependency in dependencies:
        assert contributions[dependency] == pytest.approx(
            expected[dependency], abs=tolerance(expected[dependency])
        ), dependency


def test_weighted_mean_in_a_microsimulation():
    year = 2026
    people = {
        "low": {"age": {year: 30}, "employment_income": {year: 20_000.0}},
        "high": {"age": {year: 45}, "employment_income": {year: 90_000.0}},
    }
    situation = {
        "people": people,
        "benunits": {"low": {"members": ["low"]}, "high": {"members": ["high"]}},
        "households": {
            "low": {"members": ["low"], "household_weight": {year: 1.0}},
            "high": {"members": ["high"], "household_weight": {year: 3.0}},
        },
    }
    sim = Microsimulation(situation=situation, trace=True)
    ni = sim.calculate("ni_employee", year)

    contributions = calculate_dependency_contributions(sim, "ni_employee", year)

    weighted_mean = np.average(ni.values, weights=[1.0, 3.0])
    assert weighted_mean != pytest.approx(ni.values.mean())
    assert contributions["ni_class_1_employee"] == pytest.approx(
        weighted_mean, abs=tolerance(weighted_mean)
    )


def test_map_to_and_filter():
    year = 2026
    adults = [(40, 80_000.0), (38, 30_000.0)]
    sim = traced_simulation(year, adults, [3], ["ni_employee"])
    household_ni = sim.calculate("ni_employee", year, map_to="household")

    mapped = calculate_dependency_contributions(
        sim, "ni_employee", year, map_to="household"
    )
    filtered = calculate_dependency_contributions(
        sim, "ni_employee", year, filter=np.array([False, True, False])
    )

    assert mapped["ni_class_1_employee"] == pytest.approx(
        household_ni.sum(), abs=tolerance(household_ni.sum())
    )
    second_adult = sim.calculate("ni_employee", year)[1]
    assert second_adult > 0
    assert filtered["ni_class_1_employee"] == pytest.approx(
        second_adult, abs=tolerance(second_adult)
    )


def test_existing_branch_with_the_same_name_is_left_alone():
    year, adults, child_ages = EARNER_WITH_CHILD
    sim = traced_simulation(year, adults, child_ages, ["ni_employee"])
    existing = sim.get_branch("dependency-contribution")
    existing.set_input("employment_income", year, np.array([1_000.0, 0.0]))
    existing_ni = existing.calculate("ni_employee", year)

    contributions = calculate_dependency_contributions(sim, "ni_employee", year)

    assert sim.branches["dependency-contribution"] is existing
    assert np.array_equal(existing.calculate("ni_employee", year), existing_ni)
    expected = sim.calculate("ni_employee", year).mean()
    assert contributions["ni_class_1_employee"] == pytest.approx(
        expected, abs=tolerance(expected)
    )


def test_on_a_branch():
    year, adults, child_ages = EARNER_WITH_CHILD
    sim = traced_simulation(year, adults, child_ages, ["ni_employee"])
    branch = sim.get_branch("reform")
    branch.calculate("ni_employee", year)
    sim_before, branch_before = snapshot(sim), snapshot(branch)

    on_branch = calculate_dependency_contributions(branch, "ni_employee", year)

    assert_unchanged(sim, sim_before)
    assert_unchanged(branch, branch_before)
    pd.testing.assert_series_equal(
        on_branch, calculate_dependency_contributions(sim, "ni_employee", year)
    )


def test_contribution_change_and_waterfall_chart():
    year, adults, child_ages = EARNER_WITH_CHILD
    situation = make_situation(year, adults, child_ages)
    baseline = Simulation(situation=situation, trace=True)
    reformed = Simulation(
        situation=situation,
        trace=True,
        reform={NI_MAIN_RATE: {"2026-01-01.2100-12-31": 0.12}},
    )
    for sim in (baseline, reformed):
        sim.calculate("ni_employee", year)

    change = calculate_dependency_contribution_change(
        baseline, reformed, "ni_employee", year
    )
    figure = create_waterfall_chart(baseline, "ni_employee", year)

    expected = (
        reformed.calculate("ni_employee", year).mean()
        - baseline.calculate("ni_employee", year).mean()
    )
    assert expected > 0
    assert change.loc["ni_class_1_employee", "change"] == pytest.approx(
        expected, abs=tolerance(expected)
    )
    assert isinstance(figure, go.Figure)
    assert list(figure.data[0].x) == ["ni_class_1_employee"]
