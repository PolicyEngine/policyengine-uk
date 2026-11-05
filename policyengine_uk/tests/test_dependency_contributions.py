"""Tests for calculate_dependency_contributions in policyengine_uk.utils.dependencies.

The contribution of a variable the target reads directly (a direct dependency)
is the mean of the target minus the mean of the target recalculated over the
year with that dependency zero wherever the target read it (each period, on
each branch) and every other variable the target read held at the value it
read. The trace shows which variables the target read, over which periods and
on which branch, in the latest calculation that gave the value the simulation
holds. A dependency already zero wherever the target read it contributes zero,
also to a formula that asks supplied_input or stored_as_input about what it
read. A formula that read no variables has no contributions. Where no
calculation in the trace gave the value (a stock over a period of another unit,
or a value calculated before tracing began), the reads come from running the
formula again, if it gives that value. Two cases always raise: a target set as
an input (which reads nothing), unless the system neutralizes it, and values
neither the trace nor the formula gives. Two raise where a float dependency
needs a recalculation: a target that reads its own value within the year
(recalculating it over the year replaces that value), and a read on a branch
of a subset of households (the recalculation cannot hold it). A formula that
refuses a zero raises its own error, with the dependency it zeroed.
For any household drawn below:

1. Matches a reference: each float dependency's contribution equals the one
   from a fresh simulation in which the target's float direct dependencies are
   inputs at their calculated values, except the zeroed one. The reference
   uses no branches and deletes nothing.
2. Adds up: for a target defined only by `adds` and `subtracts` of its direct
   dependencies, the contributions sum to the mean of the target, also when
   one dependency feeds another (pension contributions get tax relief).
3. Leaves the simulation as it was: the simulation holds every value it stored
   before the call, unchanged, after it, with the same records of inputs and
   model values, and gains nothing (no values, no records, no branches) apart
   from what the helper's own calculation of the target stores or drops, which
   the tests calculate first. So a second call returns the same contributions.
4. Non-float dependencies contribute zero.
5. What the simulation calculated first doesn't change the contributions: core
   can store a value with no calculation over that period, and running the
   formula again gives what the calculation it came from read.

Monthly variables are the case that broke: restoring a monthly dependency over
a year raised "Inconsistent input", because the months already held the zeros
as inputs, which did not add up to the annual value. Comparisons allow float32
rounding: the model stores values as float32.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays
from plotly import graph_objects as go

from policyengine_core import periods
from policyengine_core.entities import build_entity
from policyengine_core.parameters import ParameterNode
from policyengine_core.simulations import Simulation as CoreSimulation
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.variables import Variable as CoreVariable
from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.model_api import (
    ETERNITY,
    MONTH,
    YEAR,
    Person,
    QuantityType,
    Reform,
    Scenario,
    Variable,
)
from policyengine_uk.tests.test_housing_benefit_accommodation_dates import (
    situation as housing_benefit_situation,
)
from policyengine_uk.utils.aggregate_impact.guard import _same_array
from policyengine_uk.utils.dependencies import (
    calculate_dependency_contribution_change,
    calculate_dependency_contributions,
    calculation_again,
    create_waterfall_chart,
    get_direct_reads,
    get_variable_dependencies,
    same_values,
)
from policyengine_uk.utils.household_subset import household_subset
from policyengine_uk.utils.labour_supply_responses import response_source
from policyengine_uk.utils.measurement_branches import BEHAVIOURAL_RESPONSES
from policyengine_uk.utils.supplied_inputs import (
    CalculatedValue,
    record_model_value,
    same_array,
    stored_as_input,
    supplied_input,
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
    for i, (age, earnings, pension_contributions) in enumerate(adults):
        people[f"adult_{i}"] = {
            "age": {year: age},
            "employment_income": {year: earnings},
            "personal_pension_contributions": {year: pension_contributions},
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
EARNER_WITH_CHILD = (2026, [(40, 80_000.0, 0.0)], [3])
# Pension contributions reduce income tax through relief, so recalculating
# household_tax with them zero would move it.
EARNER_WITH_PENSION = (2026, [(40, 80_000.0, 10_000.0)], [])


@st.composite
def households(draw):
    earnings = st.one_of(
        st.just(0.0),
        st.floats(0, 250_000, allow_nan=False, allow_infinity=False),
        st.integers(0, 250_000).map(float),
    )
    pension_contributions = st.one_of(
        st.just(0.0),
        st.floats(0, 40_000, allow_nan=False, allow_infinity=False),
    )
    year = draw(st.sampled_from(YEARS))
    adults = draw(
        st.lists(
            st.tuples(st.integers(18, 90), earnings, pension_contributions),
            min_size=1,
            max_size=2,
        )
    )
    child_ages = draw(st.lists(st.integers(0, 17), max_size=3))
    return year, adults, child_ages


def traced_simulation(year, adults, child_ages, targets=TARGETS):
    sim = Simulation(situation=make_situation(year, adults, child_ages), trace=True)
    for target in targets:
        sim.calculate(target, year)
    return sim


def float_dependencies(sim, target, year):
    return [
        dependency
        for dependency in dict.fromkeys(get_variable_dependencies(target, sim, year))
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
    # to_input_dataframe exports, for every branch name.
    return set(getattr(sim, "_user_input_keys", None) or ())


def model_values(sim):
    # The model's own values (set_model_value), and the calculated values a
    # branch of the helper marks (record_model_value), with their classes.
    return {
        key: (type(value), np.array(value))
        for key, value in (getattr(sim, "_model_values", None) or {}).items()
    }


def assert_unchanged(sim, before):
    values, inputs, models, branches = before
    after = stored_values(sim)
    assert after.keys() == values.keys()
    for key, array in values.items():
        assert same_array(after[key], array), key
    assert recorded_inputs(sim) == inputs
    after_models = model_values(sim)
    assert after_models.keys() == models.keys()
    for key, (kind, array) in models.items():
        assert after_models[key][0] is kind, key
        assert same_array(after_models[key][1], array), key
    assert set(sim.branches) == branches


def snapshot(sim):
    return (
        stored_values(sim),
        recorded_inputs(sim),
        model_values(sim),
        set(sim.branches),
    )


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

    expected = {
        "ni_liable",
        "ni_class_1_employee_primary",
        "ni_class_1_employee_additional",
    }
    assert set(get_variable_dependencies("ni_class_1_employee", sim)) == expected
    assert set(get_variable_dependencies("ni_class_1_employee", sim, year)) == expected


def test_the_calculation_over_the_year_asked_for():
    # The trace shows the target over 2026 first. Its contributions in 2024
    # are those of its calculation over 2024, at 2024's NI rates.
    _, adults, child_ages = EARNER_WITH_CHILD
    sim = traced_simulation(2024, adults, child_ages, [])
    for year in (2026, 2024):
        sim.calculate("ni_class_1_employee", year)

    for year in (2024, 2026):
        contributions = calculate_dependency_contributions(
            sim, "ni_class_1_employee", year
        )
        primary = sim.calculate("ni_class_1_employee_primary", year).mean()
        mean = sim.calculate("ni_class_1_employee", year).mean()
        assert contributions["ni_class_1_employee_primary"] == pytest.approx(
            primary, abs=tolerance(primary)
        )
        assert contributions.sum() == pytest.approx(mean, abs=tolerance(mean))
    assert sim.calculate("ni_class_1_employee_primary", 2024)[0] > 0
    assert sim.calculate("ni_class_1_employee", 2024)[0] != pytest.approx(
        sim.calculate("ni_class_1_employee", 2026)[0]
    )


def test_months_calculated_before_their_year():
    # The simulation stores each month before it calculates the year, so the
    # year's trace node has a child for each month that only read the stored
    # value; the months' own calculations show what they read.
    year, adults, child_ages = EARNER_WITH_CHILD
    sim = traced_simulation(year, adults, child_ages, [])
    for month in periods.period(year).get_subperiods(periods.MONTH):
        sim.calculate("ni_class_1_employee", month)
    sim.calculate("ni_class_1_employee", year)

    contributions = calculate_dependency_contributions(sim, "ni_class_1_employee", year)

    assert set(contributions.index) == {
        "ni_liable",
        "ni_class_1_employee_primary",
        "ni_class_1_employee_additional",
    }
    mean = sim.calculate("ni_class_1_employee", year).mean()
    assert mean > 0
    assert contributions.sum() == pytest.approx(mean, abs=tolerance(mean))


def test_each_dependency_contributes_with_the_others_held():
    year, adults, child_ages = EARNER_WITH_PENSION
    sim = traced_simulation(year, adults, child_ages, ["household_net_income"])

    contributions = calculate_dependency_contributions(
        sim, "household_net_income", year
    )

    # household_tax stays at its value with the pension contributions, so they
    # contribute minus themselves, not minus themselves net of tax relief.
    for dependency, sign in [
        ("household_market_income", 1),
        ("household_benefits", 1),
        ("household_tax", -1),
        ("pension_contributions", -1),
    ]:
        expected = sign * sim.calculate(dependency, year).mean()
        assert expected != 0
        assert contributions[dependency] == pytest.approx(
            expected, abs=tolerance(expected)
        )
    mean = sim.calculate("household_net_income", year).mean()
    assert contributions.sum() == pytest.approx(mean, abs=tolerance(mean))


def test_after_an_input_changes():
    # The simulation recalculates after a new input, and the trace's latest
    # calculation shows what the current values read.
    year, adults, child_ages = EARNER_WITH_PENSION
    sim = traced_simulation(year, adults, child_ages, ["household_net_income"])
    sim.set_input("employment_income", year, np.array([30_000.0]))

    contributions = calculate_dependency_contributions(
        sim, "household_net_income", year
    )

    market_income = sim.calculate("household_market_income", year).mean()
    assert market_income == pytest.approx(30_000, abs=1)
    assert contributions["household_market_income"] == pytest.approx(
        market_income, abs=tolerance(market_income)
    )
    mean = sim.calculate("household_net_income", year).mean()
    assert contributions.sum() == pytest.approx(mean, abs=tolerance(mean))


def test_additive_targets_are_sums():
    system = Simulation(
        situation=make_situation(2026, [(40, 0.0, 0.0)], [])
    ).tax_benefit_system
    for target in ADDITIVE_TARGETS:
        variable = system.get_variable(target)
        assert not variable.formulas, target
        assert variable.adds or variable.subtracts, target


@PROPERTY_SETTINGS
@given(households())
@example(EARNER_WITH_CHILD)
@example(EARNER_WITH_PENSION)
# Found by Hypothesis: the trace shows each target over later years first.
@example((2024, [(18, 69_876.0, 0.0)], []))
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

        floats = float_dependencies(sim, target, year)
        assert set(contributions.index) == {
            dependency
            for dependency in get_variable_dependencies(target, sim, year)
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
    dependencies = float_dependencies(sim, target, year)
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
    adults = [(40, 80_000.0, 0.0), (38, 30_000.0, 0.0)]
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


# Variables that read over periods other than their own, and one that feeds
# another, added to the model by a reform.
class toy_annual(Variable):
    label = "Toy annual"
    value_type = float
    entity = Person
    definition_period = YEAR

    def formula(person, period, parameters):
        return 1_200


class toy_monthly(Variable):
    label = "Toy monthly"
    value_type = float
    entity = Person
    definition_period = MONTH

    def formula(person, period, parameters):
        return period.start.month


class toy_stock(Variable):
    label = "Toy stock"
    value_type = float
    entity = Person
    definition_period = MONTH
    quantity_type = QuantityType.STOCK

    def formula(person, period, parameters):
        return period.start.month


class toy_eternal(Variable):
    label = "Toy eternal"
    value_type = float
    entity = Person
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return 77


class toy_annual_in_january(Variable):
    label = "Toy annual in January"
    value_type = float
    entity = Person
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("toy_annual", period.first_month)


class toy_monthly_sum(Variable):
    label = "Toy monthly sum"
    value_type = float
    entity = Person
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("toy_monthly", period)


class toy_stock_at_year(Variable):
    label = "Toy stock at year"
    value_type = float
    entity = Person
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("toy_stock", period)


class toy_eternal_at_year(Variable):
    label = "Toy eternal at year"
    value_type = float
    entity = Person
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("toy_eternal", period)


class toy_double(Variable):
    label = "Toy double"
    value_type = float
    entity = Person
    definition_period = YEAR

    def formula(person, period, parameters):
        return 2 * person("toy_annual", period)


class toy_diamond(Variable):
    label = "Toy diamond"
    value_type = float
    entity = Person
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("toy_annual", period) + person("toy_double", period)


class toy_carried(Variable):
    label = "Toy carried"
    value_type = float
    entity = Person
    definition_period = YEAR

    def formula(person, period, parameters):
        # Last year's value reads this year's toy_annual, so zeroing
        # toy_annual would change it unless the function holds it.
        if period.start.year <= 2025:
            return 2 * person("toy_annual", period.offset(1))
        return person("toy_annual", period) + person("toy_carried", period.last_year)


class toy_monthly_total(Variable):
    label = "Toy monthly total"
    value_type = float
    entity = Person
    definition_period = MONTH

    def formula(person, period, parameters):
        if period.start.year <= 2025:
            return 5
        return person("toy_monthly", period) + person(
            "toy_monthly_total", period.last_month
        )


TOY_VARIABLES = [
    toy_annual,
    toy_monthly,
    toy_stock,
    toy_eternal,
    toy_annual_in_january,
    toy_monthly_sum,
    toy_stock_at_year,
    toy_eternal_at_year,
    toy_double,
    toy_diamond,
    toy_carried,
    toy_monthly_total,
]
# A target, and the contribution of each variable it reads.
TOY_CONTRIBUTIONS = [
    # A yearly variable read over a month: the function zeroes its year.
    ("toy_annual_in_january", {"toy_annual": 100}),
    # A monthly flow summed over the year.
    ("toy_monthly_sum", {"toy_monthly": 78}),
    # A monthly stock read over a year: its last month.
    ("toy_stock_at_year", {"toy_stock": 12}),
    ("toy_eternal_at_year", {"toy_eternal": 77}),
    # toy_double reads toy_annual, but the function holds it at 2,400 when it
    # zeroes toy_annual.
    ("toy_diamond", {"toy_annual": 1_200, "toy_double": 2_400}),
    # Last year's value (2,400): the function zeroes it where the target read
    # it as well as over the year, and holds it when it zeroes toy_annual.
    ("toy_carried", {"toy_annual": 1_200, "toy_carried": 2_400}),
]


class add_toy_variables(Reform):
    def apply(self):
        for variable in TOY_VARIABLES:
            self.add_variable(variable)


@pytest.fixture(scope="module")
def toy_simulation():
    situation = make_situation(2026, [(40, 0.0, 0.0)], [])
    return Simulation(situation=situation, reform=add_toy_variables, trace=True)


@pytest.mark.parametrize("target,expected", TOY_CONTRIBUTIONS)
def test_reads_over_other_periods(toy_simulation, target, expected):
    sim = toy_simulation
    sim.calculate(target, 2026)
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(sim, target, 2026)

    assert contributions.to_dict() == pytest.approx(expected)
    assert contributions.sum() == pytest.approx(sim.calculate(target, 2026).mean())
    assert_unchanged(sim, before)


def test_a_target_that_reads_its_own_earlier_months(toy_simulation):
    sim = toy_simulation
    for month in periods.period(2026).get_subperiods(periods.MONTH):
        sim.calculate("toy_monthly_total", month)

    # March: toy_monthly is 3, and February's total 2 + (1 + 5) = 8.
    contributions = calculate_dependency_contributions(
        sim, "toy_monthly_total", "2026-03"
    )
    assert contributions.to_dict() == pytest.approx(
        {"toy_monthly": 3, "toy_monthly_total": 8}
    )
    # Over the year each month reads the one before, which recalculating the
    # year replaces, so no recalculation can hold that read.
    with pytest.raises(ValueError, match="reads its own value"):
        calculate_dependency_contributions(sim, "toy_monthly_total", 2026)


def test_months_inherited_from_the_parent_simulation():
    # The branch reads the months its parent calculated, so the trace shows
    # what they read on the parent's branch.
    year, adults, child_ages = EARNER_WITH_CHILD
    sim = traced_simulation(year, adults, child_ages, [])
    for month in periods.period(year).get_subperiods(periods.MONTH):
        sim.calculate("ni_class_1_employee", month)
    branch = sim.get_branch("reform")

    contributions = calculate_dependency_contributions(
        branch, "ni_class_1_employee", year
    )

    for dependency in ["ni_class_1_employee_primary", "ni_class_1_employee_additional"]:
        expected = sim.calculate(dependency, year).mean()
        assert expected > 0
        assert contributions[dependency] == pytest.approx(
            expected, abs=tolerance(expected)
        )
    mean = branch.calculate("ni_class_1_employee", year).mean()
    assert contributions.sum() == pytest.approx(mean, abs=tolerance(mean))


def core_toy_simulation(*variables, cache_blacklist=None, parameters=None):
    system = TaxBenefitSystem([CORE_PERSON])
    # Core can't clone a system without parameters, and a branch with a
    # system of its own needs a clone.
    system.parameters = ParameterNode("", data=parameters or {})
    for variable in variables:
        system.add_variable(variable)
    if cache_blacklist:
        system.cache_blacklist = cache_blacklist
    sim = CoreSimulation(
        tax_benefit_system=system, situation={"people": {"person": {}}}, trace=True
    )
    sim.opt_out_cache = bool(cache_blacklist)
    return sim


CORE_PERSON = build_entity("person", "people", "Person", is_person=True)


class core_leaf(CoreVariable):
    label = "Core leaf"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return 10.0


class core_double(CoreVariable):
    label = "Core double"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return 2 * person("core_leaf", period)


class core_from_comparison(CoreVariable):
    label = "Core from comparison"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        sim = person.simulation
        if sim.branch_name == "comparison":
            return person("core_leaf", period)
        return sim.get_branch("comparison").calculate("core_from_comparison", period)


class core_sum_from_comparison(CoreVariable):
    label = "Core sum from comparison"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        comparison = person.simulation.get_branch("comparison")
        return comparison.calculate("core_leaf", period) + comparison.calculate(
            "core_double", period
        )


class core_branch_sensitive(CoreVariable):
    label = "Core branch sensitive"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return 10.0 if person.simulation.branch_name == "default" else 20.0


class core_with_uncached(CoreVariable):
    label = "Core with uncached"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return person("core_leaf", period) + person("core_branch_sensitive", period)


def test_reads_on_another_branch():
    sim = core_toy_simulation(
        core_leaf, core_double, core_from_comparison, core_sum_from_comparison
    )
    for target in ["core_from_comparison", "core_sum_from_comparison"]:
        sim.calculate(target, 2026)
    before = snapshot(sim)

    # Zeroed on the comparison branch the target reads: 10, not 0.
    assert calculate_dependency_contributions(
        sim, "core_from_comparison", 2026
    ).to_dict() == {"core_from_comparison": 10}
    # The target reads core_double on the comparison branch too, and the
    # function holds it there when it zeroes core_leaf.
    assert calculate_dependency_contributions(
        sim, "core_sum_from_comparison", 2026
    ).to_dict() == {"core_leaf": 10, "core_double": 20}
    assert_unchanged(sim, before)


def test_an_uncached_read_is_held_at_the_value_it_read():
    # The simulation doesn't store core_branch_sensitive (cache_blacklist),
    # and recalculating it on another branch gives 20: the trace shows the 10
    # the target read.
    sim = core_toy_simulation(
        core_leaf,
        core_branch_sensitive,
        core_with_uncached,
        cache_blacklist=["core_branch_sensitive"],
    )
    sim.calculate("core_with_uncached", 2026)
    assert sim.get_holder("core_branch_sensitive").get_array("2026") is None

    contributions = calculate_dependency_contributions(sim, "core_with_uncached", 2026)

    assert contributions.to_dict() == {"core_leaf": 10, "core_branch_sensitive": 10}


def test_the_same_variable_on_another_branch_is_a_dependency():
    person = build_entity("person", "people", "Person", is_person=True)

    class branch_leaf(CoreVariable):
        label = "Branch leaf"
        value_type = float
        entity = person
        definition_period = YEAR

        def formula(person, period):
            return 10.0

    class branch_target(CoreVariable):
        label = "Branch target"
        value_type = float
        entity = person
        definition_period = YEAR

        def formula(person, period):
            sim = person.simulation
            if sim.branch_name == "comparison":
                return person("branch_leaf", period)
            return sim.get_branch("comparison").calculate("branch_target", period)

    system = TaxBenefitSystem([person])
    system.add_variable(branch_leaf)
    system.add_variable(branch_target)
    sim = CoreSimulation(
        tax_benefit_system=system, situation={"people": {"person": {}}}, trace=True
    )
    sim.calculate("branch_target", 2026)
    [comparison] = sim.tracer.trees[0].children
    assert (comparison.name, comparison.branch_name) == (
        "branch_target",
        "comparison",
    )
    assert comparison.period == sim.tracer.trees[0].period

    assert get_variable_dependencies("branch_target", sim) == ["branch_target"]


def test_a_year_starting_in_july():
    # The function holds, and zeroes, each variable for the year from July:
    # not for the calendar year, which a yearly variable stores under another
    # key.
    year, adults, child_ages = EARNER_WITH_PENSION
    period = "year:2026-07"
    sim = traced_simulation(year, adults, child_ages, [])
    sim.calculate("household_net_income", period)

    contributions = calculate_dependency_contributions(
        sim, "household_net_income", period
    )

    market_income = sim.calculate("household_market_income", period).mean()
    assert market_income > 0
    for dependency, sign in [
        ("household_market_income", 1),
        ("household_benefits", 1),
        ("household_tax", -1),
        ("pension_contributions", -1),
    ]:
        expected = sign * sim.calculate(dependency, period).mean()
        assert contributions[dependency] == pytest.approx(
            expected, abs=tolerance(expected)
        )
    mean = sim.calculate("household_net_income", period).mean()
    assert contributions.sum() == pytest.approx(mean, abs=tolerance(mean))


def test_a_dependency_already_zero_contributes_nothing():
    # marginal_tax_rate reads household_net_income on pay-rise branches it
    # names afresh each time. Zeroing a response that is already zero, with
    # every other read held, leaves it as it was.
    year, adults, child_ages = EARNER_WITH_CHILD
    sim = traced_simulation(year, adults, child_ages, ["marginal_tax_rate"])
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(sim, "marginal_tax_rate", year)

    for response in BEHAVIOURAL_RESPONSES:
        assert not sim.calculate(response, year).any()
        assert contributions[response] == 0
    assert_unchanged(sim, before)


def test_a_labour_supply_response():
    # response_source sends a branch that shares its parent's tax-benefit
    # system to the parent's response; the new branch has a system of its own,
    # so it recalculates the response from what it read there.
    year = 2025
    target = "employment_income_behavioral_response"
    scenario = Scenario(
        parameter_changes={
            "gov.hmrc.income_tax.rates.uk[0].rate": {year: 0.30},
            "gov.simulation.labour_supply_responses.income_elasticity": {year: -0.05},
            "gov.simulation.labour_supply_responses.substitution_elasticity": {
                year: 0.25
            },
            "gov.simulation.capital_gains_responses.elasticity": {year: 0},
            "gov.simulation.capital_gains_responses.mtr_elasticity": {year: 0},
        }
    )
    sim = Simulation(
        situation=make_situation(year, [(45, 40_000.0, 0.0)], []),
        scenario=scenario,
        trace=True,
    )
    response = sim.calculate(target, year).mean()
    before = snapshot(sim)
    roots = len(sim.tracer.trees)

    contributions = calculate_dependency_contributions(sim, target, year)

    # Only calculate_dependency_contributions' own read of the target.
    assert len(sim.tracer.trees) == roots + 1
    assert response != 0
    for term in ["income_elasticity_lsr", "substitution_elasticity_lsr"]:
        expected = sim.calculate(term, year).mean()
        assert expected != 0
        assert contributions[term] == pytest.approx(expected, abs=tolerance(expected))
    assert contributions.sum() == pytest.approx(response, abs=tolerance(response))
    assert_unchanged(sim, before)


def test_a_target_that_reads_no_variables():
    sim = Simulation(situation=make_situation(2026, [(40, 0.0, 0.0)], []), trace=True)
    sim.calculate("local_bus_single_fare_share", 2026)

    contributions = calculate_dependency_contributions(
        sim, "local_bus_single_fare_share", 2026
    )

    assert contributions.empty


def test_an_enum_target_matches_the_calculation_a_formula_asked_for():
    # A formula gets an enum encoded, and Simulation.calculate decodes it for
    # its caller, so the trace's node and the caller's value read differently.
    sim = Simulation(situation=make_situation(2026, [(40, 0.0, 0.0)], []), trace=True)
    sim.calculate("uc_standard_allowance", 2026)
    value = sim.calculate("uc_standard_allowance_claimant_type", 2026)

    reads = get_direct_reads(
        "uc_standard_allowance_claimant_type", sim, 2026, value=value
    )

    assert value.dtype.kind == "U"
    assert {name for _, name in reads} == {"is_uc_single_or_joint_claimant", "age"}


def test_an_enum_target_calculated_before_tracing_began():
    # The formula runs again and gives the value the caller holds, decoded.
    target = "uc_standard_allowance_claimant_type"
    sim = Simulation(situation=make_situation(2026, [(40, 0.0, 0.0)], []))
    value = sim.calculate(target, 2026)
    sim.trace = True
    assert sim.calculate(target, 2026).tolist() == value.tolist()

    reads = get_direct_reads(target, sim, 2026, value=value)

    assert {name for _, name in reads} == {"is_uc_single_or_joint_claimant", "age"}


@pytest.mark.parametrize(
    "target,message",
    [
        # birth_instant rejects an age of zero with the date of birth the real
        # age gave, which the recalculation holds.
        ("state_pension_age", "'age' zero .*Set age to the age on 6 October"),
        # No category fits no bedrooms.
        ("LHA_category", "'LHA_allowed_bedrooms' zero .*Invalid value"),
    ],
)
def test_a_formula_that_refuses_a_zero_raises_its_own_error(target, message):
    sim = Simulation(situation=make_situation(2026, [(40, 0.0, 0.0)], []), trace=True)
    sim.calculate(target, 2026)
    before = snapshot(sim)

    with pytest.raises(ValueError, match=message):
        calculate_dependency_contributions(sim, target, 2026)

    assert_unchanged(sim, before)


class core_from_fresh_branch(CoreVariable):
    label = "Core from a fresh branch"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        # A name no branch has, and the branch removed after reading it, as
        # marginal_tax_rate and measurement branches do.
        sim = person.simulation
        name = "fresh"
        while name in sim.branches or name == sim.branch_name:
            name += "_"
        branch = sim.get_branch(name)
        try:
            return branch.calculate("core_leaf", period) + branch.calculate(
                "core_double", period
            )
        finally:
            del sim.branches[name]


class core_from_same_system(CoreVariable):
    label = "Core from the nearest ancestor with the same system"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        source = response_source(person.simulation)
        if source is not person.simulation:
            return source.calculate("core_from_same_system", period)
        return person("core_leaf", period) + person("core_double", period)


class core_switch(CoreVariable):
    label = "Core switch"
    value_type = bool
    entity = CORE_PERSON
    definition_period = YEAR


class core_twenty(CoreVariable):
    label = "Core twenty"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return 20.0


class core_chosen(CoreVariable):
    label = "Core chosen"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        if person("core_switch", period).any():
            return person("core_twenty", period)
        return person("core_leaf", period)


class core_annual(CoreVariable):
    label = "Core annual"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return 1200.0


class core_january_and_leaf(CoreVariable):
    label = "Core January and leaf"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return person("core_annual", period.first_month) + person("core_leaf", period)


class core_input(CoreVariable):
    label = "Core input"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR
    default_value = 10.0


class core_from_input(CoreVariable):
    label = "Core from input"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return person("core_input", period)


class core_restarting(CoreVariable):
    label = "Core restarting"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        # The input set while calculating makes core calculate it again.
        value = person("core_from_input", period) + person("core_twenty", period)
        person.simulation.set_input("core_input", period, [20.0])
        return value


class core_sets_itself(CoreVariable):
    label = "Core sets itself"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        person.simulation.set_input("core_sets_itself", period, [10.0])
        return person("core_sets_itself", period)


class core_from_july(CoreVariable):
    label = "Core from July"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        if period.start.month == 7:
            return 2 * person("core_leaf", period.this_year.offset(1, YEAR))
        return person("core_leaf", period) + person("core_from_july", "year:2025-07")


class core_month_stock(CoreVariable):
    label = "Core month stock"
    value_type = float
    entity = CORE_PERSON
    definition_period = MONTH
    quantity_type = QuantityType.STOCK

    def formula(person, period):
        return 10.0 * period.start.month


class core_stock_and_leaf(CoreVariable):
    label = "Core stock and leaf"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        # A monthly stock over a year is its December value.
        return person("core_leaf", period) + person("core_month_stock", period)


class core_leaf_and_double(CoreVariable):
    label = "Core leaf and double"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return person("core_leaf", period) + person("core_double", period)


class core_monthly_leaf(CoreVariable):
    label = "Core monthly leaf"
    value_type = float
    entity = CORE_PERSON
    definition_period = MONTH

    def formula(person, period):
        return person("core_leaf", period.this_year) / 12


def test_reads_on_a_branch_named_afresh():
    sim = core_toy_simulation(core_leaf, core_double, core_from_fresh_branch)
    sim.calculate("core_from_fresh_branch", 2026)
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(
        sim, "core_from_fresh_branch", 2026
    )

    assert contributions.to_dict() == {"core_leaf": 10, "core_double": 20}
    assert_unchanged(sim, before)


def test_a_formula_that_reads_the_nearest_ancestor_with_its_system():
    sim = core_toy_simulation(core_leaf, core_double, core_from_same_system)
    sim.calculate("core_from_same_system", 2026)
    roots = len(sim.tracer.trees)

    contributions = calculate_dependency_contributions(
        sim, "core_from_same_system", 2026
    )

    assert contributions.to_dict() == {"core_leaf": 10, "core_double": 20}
    # Only calculate_dependency_contributions' own read of the target.
    assert len(sim.tracer.trees) == roots + 1


def test_a_branch_holds_what_its_parent_held_when_it_was_created():
    root = core_toy_simulation(
        core_leaf,
        core_twenty,
        core_switch,
        core_chosen,
        core_annual,
        core_january_and_leaf,
    )
    parent = root.get_branch("parent")
    parent.calculate("core_chosen", 2026)
    parent.calculate("core_annual", "2026-01")
    branch = parent.get_branch("scenario")
    branch.calculate("core_january_and_leaf", 2026)
    # The parent then reads another variable, and another annual value.
    parent.set_input("core_switch", 2026, [True])
    parent.calculate("core_chosen", 2026)
    parent.set_input("core_annual", 2026, [2400.0])
    parent.calculate("core_annual", 2026)

    assert calculate_dependency_contributions(
        branch, "core_chosen", 2026
    ).to_dict() == {"core_switch": 0, "core_leaf": 10}
    assert calculate_dependency_contributions(
        branch, "core_january_and_leaf", 2026
    ).to_dict() == {"core_annual": 100, "core_leaf": 10}


def test_a_calculation_that_restarts():
    sim = core_toy_simulation(core_input, core_from_input, core_twenty, core_restarting)
    branch = sim.get_branch("scenario")
    assert branch.calculate("core_restarting", 2026) == 40

    contributions = calculate_dependency_contributions(branch, "core_restarting", 2026)

    # The values of the calculation that gave 40, not of the first attempt.
    assert contributions.to_dict() == {"core_from_input": 20, "core_twenty": 20}


def test_a_target_that_sets_itself_as_an_input():
    # Its formula sets its own value as an input, which reads nothing, and
    # then reads it: a ValueError, not a RecursionError.
    sim = core_toy_simulation(core_sets_itself)
    sim.calculate("core_sets_itself", 2026)

    with pytest.raises(ValueError, match="as an input"):
        calculate_dependency_contributions(sim, "core_sets_itself", 2026)


def test_a_core_target_that_reads_no_variables():
    sim = core_toy_simulation(core_leaf)
    sim.calculate("core_leaf", 2026)

    assert calculate_dependency_contributions(sim, "core_leaf", 2026).empty


def test_its_own_value_over_a_year_starting_in_july():
    # year:2025-07 overlaps 2026, but core stores it under another key.
    sim = core_toy_simulation(core_leaf, core_from_july)
    sim.calculate("core_from_july", 2026)

    contributions = calculate_dependency_contributions(sim, "core_from_july", 2026)

    assert contributions.to_dict() == {"core_leaf": 10, "core_from_july": 20}


@pytest.mark.parametrize("cache_blacklist", [None, ["core_month_stock"]])
def test_a_monthly_stock_read_over_a_year_is_held_at_december(cache_blacklist):
    sim = core_toy_simulation(
        core_leaf,
        core_month_stock,
        core_stock_and_leaf,
        cache_blacklist=cache_blacklist,
    )
    assert sim.calculate("core_stock_and_leaf", 2026) == 130

    contributions = calculate_dependency_contributions(sim, "core_stock_and_leaf", 2026)

    assert contributions.to_dict() == {"core_leaf": 10, "core_month_stock": 120}


def test_a_core_target_set_as_an_input_raises():
    # The trace shows a calculation that read the leaf and the double, but
    # the value it holds now is an input, which reads nothing.
    sim = core_toy_simulation(core_leaf, core_double, core_leaf_and_double)
    assert sim.calculate("core_leaf_and_double", 2026) == 30
    sim.set_input("core_leaf_and_double", 2026, [100.0])
    before = snapshot(sim)

    with pytest.raises(ValueError, match="as an input"):
        calculate_dependency_contributions(sim, "core_leaf_and_double", 2026)
    assert_unchanged(sim, before)


@pytest.mark.parametrize("calculated_first", [False, True])
def test_household_net_income_set_as_an_input_raises(calculated_first):
    year, adults, child_ages = EARNER_WITH_PENSION
    sim = Simulation(situation=make_situation(year, adults, child_ages), trace=True)
    if calculated_first:
        assert sim.calculate("household_net_income", year)[0] != 100_000
    sim.set_input("household_net_income", year, [100_000.0])
    # The calculation after an input changes drops the values calculated
    # before it, as any calculation does.
    assert sim.calculate("household_net_income", year).tolist() == [100_000]
    before = snapshot(sim)

    with pytest.raises(ValueError, match="as an input"):
        calculate_dependency_contributions(sim, "household_net_income", year)
    assert_unchanged(sim, before)


@pytest.mark.parametrize("calculated_first", [False, True])
def test_the_dependencies_of_a_target_set_as_an_input_raise(calculated_first):
    # An input reads nothing, whatever a calculation of it read before, and
    # whatever its formula would read.
    sim = core_toy_simulation(core_leaf, core_double)
    if calculated_first:
        sim.calculate("core_double", 2026)
    sim.set_input("core_double", 2026, [5.0])
    sim.calculate("core_double", 2026)

    with pytest.raises(ValueError, match="as an input"):
        get_variable_dependencies("core_double", sim, 2026)


def test_values_no_calculation_gave_raise():
    # The trace shows the calculation of 30, not where 99 came from.
    sim = core_toy_simulation(core_leaf, core_double, core_leaf_and_double)
    sim.calculate("core_leaf_and_double", 2026)
    sim.get_holder("core_leaf_and_double").put_in_cache(
        np.array([99.0]), periods.period(2026), sim.branch_name, derived=True
    )
    assert sim.calculate("core_leaf_and_double", 2026) == 99

    with pytest.raises(ValueError, match="no calculation in the trace gave"):
        calculate_dependency_contributions(sim, "core_leaf_and_double", 2026)


def test_a_monthly_core_target_over_a_year():
    sim = core_toy_simulation(core_leaf, core_monthly_leaf)
    assert sim.calculate("core_monthly_leaf", 2026) == pytest.approx(10)

    contributions = calculate_dependency_contributions(sim, "core_monthly_leaf", 2026)

    assert contributions.to_dict() == pytest.approx({"core_leaf": 10})


def test_a_month_set_as_an_input_raises():
    # The year sums its months, and March, an input, reads nothing.
    sim = core_toy_simulation(core_leaf, core_monthly_leaf)
    sim.set_input("core_monthly_leaf", "2026-03", [5.0])
    assert sim.calculate("core_monthly_leaf", 2026) == pytest.approx(10 * 11 / 12 + 5)

    with pytest.raises(
        ValueError, match="'core_monthly_leaf' over 2026-03 as an input"
    ):
        calculate_dependency_contributions(sim, "core_monthly_leaf", 2026)


def test_a_month_stored_directly_raises():
    # The year sums the months stored, and March's calculation gave 10 / 12,
    # not the 5 stored over it.
    sim = core_toy_simulation(core_leaf, core_monthly_leaf)
    for month in periods.period(2026).get_subperiods(MONTH):
        sim.calculate("core_monthly_leaf", month)
    sim.get_holder("core_monthly_leaf").put_in_cache(
        np.array([5.0]), periods.period("2026-03"), sim.branch_name, derived=True
    )
    assert sim.calculate("core_monthly_leaf", 2026) == pytest.approx(10 * 11 / 12 + 5)

    with pytest.raises(ValueError, match="no calculation in the trace gave"):
        calculate_dependency_contributions(sim, "core_monthly_leaf", 2026)


def test_values_stored_over_a_formula_that_reads_nothing_raise():
    # The formula gives 10 and reads nothing, which doesn't explain the 99.
    sim = core_toy_simulation(core_leaf)
    sim.calculate("core_leaf", 2026)
    sim.get_holder("core_leaf").put_in_cache(
        np.array([99.0]), periods.period(2026), sim.branch_name, derived=True
    )
    assert sim.calculate("core_leaf", 2026) == 99

    with pytest.raises(ValueError, match="no calculation in the trace gave"):
        calculate_dependency_contributions(sim, "core_leaf", 2026)


@pytest.mark.parametrize(
    "target,expected",
    [
        ("core_leaf_and_double", {"core_leaf": 10, "core_double": 20}),
        ("core_monthly_leaf", {"core_leaf": 10}),
    ],
)
def test_values_calculated_before_tracing_began(target, expected):
    # The trace shows only a read of the stored value, and the formula gives
    # that value again and shows what it reads.
    sim = core_toy_simulation(
        core_leaf, core_double, core_leaf_and_double, core_monthly_leaf
    )
    sim.trace = False
    sim.calculate(target, 2026)
    sim.trace = True
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(sim, target, 2026)

    assert contributions.to_dict() == pytest.approx(expected)
    assert_unchanged(sim, before)


def test_a_month_calculated_before_tracing_began():
    # The year's node shows only a read of March's stored value, and March's
    # formula gives that value again.
    sim = core_toy_simulation(core_leaf, core_monthly_leaf)
    sim.trace = False
    sim.calculate("core_monthly_leaf", "2026-03")
    sim.trace = True
    assert sim.calculate("core_monthly_leaf", 2026) == pytest.approx(10)
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(sim, "core_monthly_leaf", 2026)

    assert contributions.to_dict() == pytest.approx({"core_leaf": 10})
    assert_unchanged(sim, before)


def test_a_variable_the_trace_does_not_show_raises():
    sim = core_toy_simulation(core_leaf, core_double)
    sim.calculate("core_leaf", 2026)

    with pytest.raises(ValueError, match="The trace shows no calculation"):
        get_variable_dependencies("core_double", sim, 2026)


def test_running_the_formula_again_matches_the_trace():
    # A clone that starts tracing holds values it did not calculate, so running
    # each formula again gives the reads, where the traced simulation has them
    # from its trace.
    year, adults, child_ages = EARNER_WITH_PENSION
    situation = make_situation(year, adults, child_ages)
    untraced = Simulation(situation=situation)
    traced = traced_simulation(year, adults, child_ages)
    for target in TARGETS:
        untraced.calculate(target, year)
    clone = untraced.clone(trace=True)

    for target in TARGETS:
        again = calculate_dependency_contributions(clone, target, year)
        expected = calculate_dependency_contributions(traced, target, year)
        assert again.to_dict() == pytest.approx(expected.to_dict(), abs=tolerance(1))


class core_year_stock(CoreVariable):
    label = "Core year stock"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR
    quantity_type = QuantityType.STOCK

    def formula(person, period):
        return 3 * person("core_leaf", period)


class core_month_stock_of_leaf(CoreVariable):
    label = "Core month stock of leaf"
    value_type = float
    entity = CORE_PERSON
    definition_period = MONTH
    quantity_type = QuantityType.STOCK

    def formula(person, period):
        return person("core_leaf", period.this_year) * period.start.month


class core_eternal_of_leaf(CoreVariable):
    label = "Core eternal of leaf"
    value_type = float
    entity = CORE_PERSON
    definition_period = ETERNITY

    def formula(person, period):
        return 2 * person("core_leaf", period.this_year)


class core_year_stock_from_input(CoreVariable):
    label = "Core year stock from input"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR
    quantity_type = QuantityType.STOCK

    def formula(person, period):
        return person("core_input", period)


class core_december_carries(CoreVariable):
    label = "Core December carries"
    value_type = float
    entity = CORE_PERSON
    definition_period = MONTH

    def formula(person, period):
        monthly = person("core_monthly_leaf", period)
        if period.start.month == 12:
            return monthly + person("core_december_carries", period.last_month)
        return monthly


def period_toy_simulation():
    return core_toy_simulation(
        core_leaf,
        core_double,
        core_monthly_leaf,
        core_year_stock,
        core_month_stock_of_leaf,
        core_eternal_of_leaf,
        core_december_carries,
    )


@pytest.mark.parametrize(
    "name,first,asked,expected",
    [
        ("core_year_stock", 2026, "2026-03", 30),
        ("core_year_stock", "2026-03", 2026, 30),
        ("core_year_stock", "2026-07", "2026-03", 30),
        ("core_year_stock", 2026, "month:2026-01:3", 30),
        ("core_month_stock_of_leaf", "2026-12", 2026, 120),
        ("core_month_stock_of_leaf", 2026, "2026-12", 120),
        ("core_month_stock_of_leaf", "2027-06", "year:2026-07", 60),
        ("core_month_stock_of_leaf", "year:2026-07", "2027-06", 60),
        ("core_eternal_of_leaf", 2025, 2026, 20),
    ],
)
def test_a_value_core_keeps_under_another_period(name, first, asked, expected):
    # Core keeps one value of a stock under its definition period, and of an
    # eternal variable under eternity. The formula runs under the node of the
    # first period asked for, and any other period's node shows no reads.
    sim = period_toy_simulation()
    sim.calculate(name, first)
    assert sim.calculate(name, asked) == expected
    before = snapshot(sim)
    roots = len(sim.tracer.trees)

    contributions = calculate_dependency_contributions(sim, name, asked)

    assert contributions.to_dict() == {"core_leaf": expected}
    assert_unchanged(sim, before)
    assert len(sim.tracer.trees) == roots + 1


@pytest.mark.parametrize(
    "target,expected",
    [
        (
            "total_wealth",
            {
                "savings": 3_000,
                "property_wealth": 0,
                "corporate_wealth": 0,
                "private_pension_wealth": 0,
            },
        ),
        ("cash_isa_countable_capital", {"cash_isa_balance": 2_000, "cash_isa": 2_000}),
    ],
)
@pytest.mark.parametrize(
    "first,asked",
    [(None, "2026-03"), (2026, "2026-03"), ("2026-03", 2026), ("2026-07", "2026-03")],
)
def test_a_real_stock_calculated_over_another_period(target, expected, first, asked):
    sim = Simulation(
        situation={
            "age": {2026: 40},
            "savings": {2026: 3_000.0},
            "cash_isa_balance": {2026: 2_000.0},
        },
        trace=True,
    )
    if first is not None:
        sim.calculate(target, first)
    sim.calculate(target, asked)
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(sim, target, asked)

    assert contributions.to_dict() == pytest.approx(expected)
    assert_unchanged(sim, before)
    assert set(get_variable_dependencies(target, sim, asked)) == set(expected)


@pytest.mark.parametrize("first,asked", [(2026, "2026-03"), ("2026-03", 2026)])
def test_a_real_stock_in_a_microsimulation_and_on_a_subset_of_it(first, asked):
    people = {name: {"age": {2026: 40}} for name in ("a", "b")}
    situation = {
        "people": people,
        "benunits": {name: {"members": [name]} for name in people},
        "households": {
            "a": {
                "members": ["a"],
                "household_weight": {2026: 1.0},
                "savings": {2026: 3_000.0},
            },
            "b": {
                "members": ["b"],
                "household_weight": {2026: 3.0},
                "savings": {2026: 5_000.0},
            },
        },
    }
    expected = {
        "savings": 4_500,
        "property_wealth": 0,
        "corporate_wealth": 0,
        "private_pension_wealth": 0,
    }
    sim = Microsimulation(situation=situation, trace=True)
    sim.calculate("total_wealth", first)
    sim.calculate("total_wealth", asked)
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(sim, "total_wealth", asked)

    assert contributions.to_dict() == pytest.approx(expected)
    assert_unchanged(sim, before)

    with household_subset(sim, "first", np.array([True, False])) as subset:
        subset.simulation.calculate("total_wealth", first)

        contributions = calculate_dependency_contributions(
            subset.simulation, "total_wealth", asked
        )

    assert contributions.to_dict() == pytest.approx({**expected, "savings": 3_000})


def test_a_stock_a_branch_kept_from_its_parent():
    # The branch holds what its parent held when the parent made it, and the
    # formula, run on a branch of it, reads those values.
    name = "core_year_stock_from_input"
    root = core_toy_simulation(core_input, core_year_stock_from_input)
    parent = root.get_branch("parent")
    parent.set_input("core_input", 2026, [10.0])
    assert parent.calculate(name, 2026) == 10
    branch = parent.get_branch("kept")
    parent.set_input("core_input", 2026, [20.0])
    assert parent.calculate(name, 2026) == 20
    assert branch.calculate(name, "2026-03") == 10

    contributions = calculate_dependency_contributions(branch, name, "2026-03")

    assert contributions.to_dict() == {"core_input": 10}


def test_a_sum_core_stored_with_no_node_over_the_year():
    # calculate_add shows each month, and stores the year with no node of it.
    sim = core_toy_simulation(core_leaf, core_monthly_leaf)
    assert sim.calculate_add("core_monthly_leaf", 2026) == pytest.approx(10)
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(sim, "core_monthly_leaf", 2026)

    assert contributions.to_dict() == pytest.approx({"core_leaf": 10})
    assert_unchanged(sim, before)


def test_a_twelfth_core_stored_with_no_node_over_the_month():
    # calculate_divide shows the year, and stores the month with no node of it.
    sim = core_toy_simulation(core_leaf, core_double)
    assert sim.calculate_divide("core_double", "2026-03") == pytest.approx(20 / 12)
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(sim, "core_double", "2026-03")

    assert contributions.to_dict() == pytest.approx({"core_leaf": 20 / 12})
    assert_unchanged(sim, before)


@pytest.mark.parametrize("before_tracing", [False, True])
def test_a_month_that_reads_its_own_earlier_month_over_a_year(before_tracing):
    # December reads November, which recalculating the year replaces, whether
    # the trace shows that read or running the formula again does.
    sim = period_toy_simulation()
    if before_tracing:
        sim.trace = False
    sim.calculate("core_december_carries", 2026)
    if before_tracing:
        sim.trace = True
    sim.calculate("core_december_carries", 2026)
    before = snapshot(sim)

    reads = get_direct_reads("core_december_carries", sim, 2026)

    assert list(reads[(None, "core_december_carries")]) == [periods.period("2026-11")]
    assert len(reads[(None, "core_monthly_leaf")]) == 12
    with pytest.raises(
        ValueError, match="reads its own value over 2026-11, within 2026"
    ):
        calculate_dependency_contributions(sim, "core_december_carries", 2026)
    assert_unchanged(sim, before)


def contributions_or_error(sim, name, asked):
    try:
        return calculate_dependency_contributions(sim, name, asked).to_dict()
    except ValueError as error:
        return str(error)


@settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    name=st.sampled_from(
        [
            "core_double",
            "core_monthly_leaf",
            "core_year_stock",
            "core_month_stock_of_leaf",
            "core_eternal_of_leaf",
            "core_december_carries",
        ]
    ),
    first=st.lists(
        st.sampled_from(["2026", "2026-03", "2026-07", "2026-12", "year:2026-07"]),
        max_size=3,
    ),
    asked=st.sampled_from(["2026", "2026-03", "2026-12", "year:2026-07"]),
    before_tracing=st.booleans(),
)
def test_contributions_do_not_depend_on_what_the_simulation_calculated_first(
    name, first, asked, before_tracing
):
    fresh = contributions_or_error(period_toy_simulation(), name, asked)
    sim = period_toy_simulation()
    if before_tracing:
        sim.trace = False
    for period in first:
        sim.calculate(name, period)
    if before_tracing:
        sim.trace = True
    sim.calculate(name, asked)
    before = snapshot(sim)

    contributions = contributions_or_error(sim, name, asked)

    if isinstance(fresh, str):
        assert contributions == fresh
    else:
        assert contributions == pytest.approx(fresh)
    assert_unchanged(sim, before)


class core_leaf_while_active(CoreVariable):
    label = "Core leaf while active"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period, parameters):
        if not parameters(period).active:
            return 0.0
        return person("core_leaf", period)


class core_monthly_while_active(CoreVariable):
    label = "Core monthly while active"
    value_type = float
    entity = CORE_PERSON
    definition_period = MONTH

    def formula(person, period, parameters):
        if not parameters(period).active:
            return 0.0
        return person("core_leaf", period.this_year) / 12


@pytest.mark.parametrize("on_a_branch", [False, True])
@pytest.mark.parametrize(
    "variable", [core_leaf_while_active, core_monthly_while_active]
)
def test_a_later_calculation_that_reads_only_a_parameter(variable, on_a_branch):
    # The formula now returns before it reads a variable, so what its earlier
    # calculation read doesn't explain the zero.
    name = variable.__name__
    sim = core_toy_simulation(
        core_leaf,
        variable,
        parameters={"active": {"values": {"2026-01-01": True}}},
    )
    assert sim.calculate(name, 2026) == pytest.approx(10)
    target = sim.get_branch("closed", clone_system=True) if on_a_branch else sim
    target.tax_benefit_system.modify_parameters({"active": {"2026": False}})
    target.delete_arrays(name, 2026)
    assert target.calculate(name, 2026) == 0

    assert calculate_dependency_contributions(target, name, 2026).empty


@pytest.mark.parametrize("on_a_branch", [False, True])
def test_a_later_calculation_that_reads_only_a_parameter_and_gives_the_same_value(
    on_a_branch,
):
    # The latest calculation that gave the zero read no variables, though an
    # earlier one that read core_leaf gave it too.
    name = "core_leaf_while_active"
    sim = core_toy_simulation(
        core_leaf,
        core_leaf_while_active,
        parameters={"active": {"values": {"2026-01-01": True}}},
    )
    sim.set_input("core_leaf", 2026, [0.0])
    assert sim.calculate(name, 2026) == 0
    target = sim.get_branch("closed", clone_system=True) if on_a_branch else sim
    target.tax_benefit_system.modify_parameters({"active": {"2026": False}})
    target.delete_arrays(name, 2026)
    assert target.calculate(name, 2026) == 0

    assert calculate_dependency_contributions(target, name, 2026).empty


def constant_formula(name, definition):
    # A version of the variable called name whose formula reads nothing, for
    # a system to replace it with: its node looks like a read of a stored value.
    class constant(CoreVariable):
        label = "Constant"
        value_type = float
        entity = CORE_PERSON
        definition_period = definition

        def formula(person, period):
            return 0.0

    constant.__name__ = name
    return constant


@pytest.mark.parametrize("on_a_branch", [False, True])
@pytest.mark.parametrize(
    "name,variables,definition",
    [
        ("core_leaf_and_double", (core_double, core_leaf_and_double), YEAR),
        ("core_monthly_leaf", (core_monthly_leaf,), MONTH),
    ],
)
def test_a_later_formula_that_reads_nothing(name, variables, definition, on_a_branch):
    sim = core_toy_simulation(core_leaf, *variables)
    assert sim.calculate(name, 2026) > 0
    target = sim.get_branch("closed", clone_system=True) if on_a_branch else sim
    target.tax_benefit_system.update_variable(constant_formula(name, definition))
    target.delete_arrays(name, 2026)
    assert target.calculate(name, 2026) == 0
    before = snapshot(target)
    roots = len(target.tracer.trees)

    assert calculate_dependency_contributions(target, name, 2026).empty

    # Running the formula again left the values, the records, the branches and
    # the trace as they were. The one new root is the function's own
    # calculation of the target.
    assert_unchanged(target, before)
    assert len(target.tracer.trees) == roots + 1


@pytest.mark.parametrize("set_as_an_input", [False, True])
def test_a_neutralized_target_reads_nothing(set_as_an_input):
    # It reads as its default, whatever its parent's calculation read and
    # whatever the branch holds.
    name = "core_leaf_and_double"
    sim = core_toy_simulation(core_leaf, core_double, core_leaf_and_double)
    assert sim.calculate(name, 2026) == 30
    branch = sim.get_branch("neutralized", clone_system=True)
    if set_as_an_input:
        branch.set_input(name, 2026, [5.0])
    branch.tax_benefit_system.neutralize_variable(name)
    assert branch.calculate(name, 2026) == 0

    assert calculate_dependency_contributions(branch, name, 2026).empty


def test_a_formula_that_returns_before_it_reads_a_variable():
    # With the scheme closed on the branch, lifetime_isa_bonus returns before
    # it reads a variable, so the age and payments its parent's calculation
    # read don't explain the branch's zero.
    class close_the_lifetime_isa(Reform):
        def apply(self):
            self.modify_parameters({"gov.hmrc.isa.lifetime.in_effect": {"2026": False}})

    year = 2026
    sim = Simulation(
        situation={
            "people": {
                "person": {"age": {year: 30}, "lifetime_isa_payments": {year: 4_000.0}}
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        },
        trace=True,
    )
    assert sim.calculate("lifetime_isa_bonus", year).tolist() == [1_000]
    branch = sim.get_branch("closed", clone_system=True)
    branch.apply_reform(close_the_lifetime_isa)
    assert branch.calculate("lifetime_isa_bonus", year).tolist() == [0]
    before = snapshot(branch)

    assert calculate_dependency_contributions(branch, "lifetime_isa_bonus", year).empty
    assert_unchanged(branch, before)
    # On the parent, it still reads the payments.
    assert (
        calculate_dependency_contributions(sim, "lifetime_isa_bonus", year)[
            "lifetime_isa_payments"
        ]
        == 1_000
    )


def test_running_a_formula_again():
    sim = core_toy_simulation(core_leaf, core_double, core_leaf_and_double)
    year = periods.period(2026)
    sim.calculate("core_leaf_and_double", year)
    # Its formula gives the value and reads nothing.
    assert calculation_again(sim, "core_leaf", year, np.array([10.0])).children == []
    # Its formula gives another value.
    assert calculation_again(sim, "core_leaf", year, np.array([99.0])) is None
    # Its formula gives the value and reads variables, as if on sim's branch.
    node = calculation_again(sim, "core_leaf_and_double", year, np.array([30.0]))
    assert [(child.name, child.branch_name) for child in node.children] == [
        ("core_leaf", sim.branch_name),
        ("core_double", sim.branch_name),
    ]
    assert node.branch_name == sim.branch_name
    # Without a value it takes what the formula gives. Nothing holds the double
    # here, so the formula calculates it, and shows what it read.
    fresh = core_toy_simulation(core_leaf, core_double, core_leaf_and_double)
    node = calculation_again(fresh, "core_leaf_and_double", year)
    assert node.children[1].children[0].name == "core_leaf"
    assert node.children[1].children[0].branch_name == fresh.branch_name
    assert set(sim.branches) == set(fresh.branches) == set()


class core_monthly_leaf_and_leaf(CoreVariable):
    label = "Core monthly leaf and leaf"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return person("core_monthly_leaf", period) + person("core_leaf", period)


def test_running_a_formula_again_on_a_household_subset():
    # A limitation the docstring lists, under what a formula reads from another
    # simulation: on a subset, months_since_last_birthday takes the whole
    # population's value, which the run's tracer does not show and the source
    # simulation's trace does.
    name = "months_since_last_birthday"
    people = {person: {"age": {2026: 40}} for person in ("a", "b")}
    sim = Simulation(
        situation={
            "people": people,
            "benunits": {person: {"members": [person]} for person in people},
            "households": {person: {"members": [person]} for person in people},
        },
        trace=True,
    )
    with household_subset(sim, "first", np.array([True, False])) as subset:
        value = subset.simulation.calculate(name, 2026)
        roots = len(sim.tracer.trees)

        node = calculation_again(subset.simulation, name, periods.period(2026), value)

    assert node.children == []
    assert len(sim.tracer.trees) == roots + 1


def test_running_a_formula_again_holds_an_uncached_read_of_each_month():
    # Nothing stores the months, so the value of each comes from the node of
    # the read, under the wrapper of its year.
    sim = core_toy_simulation(
        core_leaf,
        core_monthly_leaf,
        core_monthly_leaf_and_leaf,
        cache_blacklist=["core_monthly_leaf"],
    )
    sim.trace = False
    assert sim.calculate("core_monthly_leaf_and_leaf", 2026) == pytest.approx(20)
    sim.trace = True

    contributions = calculate_dependency_contributions(
        sim, "core_monthly_leaf_and_leaf", 2026
    )

    assert contributions.to_dict() == pytest.approx(
        {"core_monthly_leaf": 10, "core_leaf": 10}
    )


@pytest.mark.parametrize("target", ["lifetime_isa_bonus", "age_under_18"])
def test_a_neutralized_target_equal_to_what_its_formula_gave(target):
    # The earlier calculation read the age and gave the zero or the false that
    # the default equals, but the neutralized variable reads nothing.
    sim = Simulation(situation={"age": {2026: 40}}, trace=True)
    sim.calculate(target, 2026)
    branch = sim.get_branch("neutralized", clone_system=True)
    branch.tax_benefit_system.neutralize_variable(target)
    branch.calculate(target, 2026)

    assert calculate_dependency_contributions(branch, target, 2026).empty
    assert get_variable_dependencies(target, branch, 2026) == []


def test_a_constant_equal_to_what_the_formula_it_replaced_gave():
    # A limitation the docstring lists: a constant leaves no calculation in the
    # index, so the reads come from the calculation that gave equal values.
    name = "core_zero_from_leaf"

    class core_zero_from_leaf(CoreVariable):
        label = "Core zero from leaf"
        value_type = float
        entity = CORE_PERSON
        definition_period = YEAR

        def formula(person, period):
            return person("core_leaf", period) - 10

    sim = core_toy_simulation(core_leaf, core_zero_from_leaf)
    assert sim.calculate(name, 2026) == 0
    branch = sim.get_branch("constant", clone_system=True)
    branch.tax_benefit_system.update_variable(constant_formula(name, YEAR))
    branch.delete_arrays(name, 2026)
    assert branch.calculate(name, 2026) == 0

    contributions = calculate_dependency_contributions(branch, name, 2026)

    assert contributions.to_dict() == {"core_leaf": 0}


class core_raises(CoreVariable):
    label = "Core raises"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        raise RuntimeError("no value")


class core_catches_a_failed_read(CoreVariable):
    label = "Core catches a failed read"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        try:
            person("core_raises", period)
        except RuntimeError:
            pass
        return person("core_leaf", period)


class core_catches_its_own_month(CoreVariable):
    label = "Core catches its own month"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        try:
            person("core_catches_its_own_month", period.first_month)
        except Exception:
            pass
        return person("core_leaf", period)


def test_a_formula_that_raises_when_it_runs_again():
    # A caller stored the value over a formula that raises: the error reaches
    # the caller, and the branch that ran the formula goes.
    sim = core_toy_simulation(core_raises)
    sim.get_holder("core_raises").put_in_cache(
        np.array([5.0]), periods.period(2026), sim.branch_name, derived=True
    )
    assert sim.calculate("core_raises", 2026) == 5
    before = snapshot(sim)

    with pytest.raises(RuntimeError, match="no value"):
        calculate_dependency_contributions(sim, "core_raises", 2026)

    assert_unchanged(sim, before)


class core_reads_then_raises(CoreVariable):
    label = "Core reads then raises"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        person("core_leaf", period)
        raise RuntimeError("no value")


class core_catches_a_late_failure(CoreVariable):
    label = "Core catches a late failure"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        try:
            person("core_reads_then_raises", period)
        except RuntimeError:
            pass
        return person("core_leaf", period)


def test_what_a_calculation_read_before_it_raised_gave_no_value():
    # The trace shows the node with what it read and no value, so the formula
    # runs again, and its error reaches the caller.
    sim = core_toy_simulation(
        core_leaf, core_reads_then_raises, core_catches_a_late_failure
    )
    assert sim.calculate("core_catches_a_late_failure", 2026) == 10

    with pytest.raises(RuntimeError, match="no value"):
        get_direct_reads("core_reads_then_raises", sim, 2026)
    contributions = calculate_dependency_contributions(
        sim, "core_catches_a_late_failure", 2026
    )

    assert contributions.to_dict() == {"core_leaf": 10}


@pytest.mark.parametrize(
    "name", ["core_catches_a_failed_read", "core_catches_its_own_month"]
)
def test_a_formula_that_catches_a_failed_read(name):
    # The read raised, so it gave the formula nothing, and the recalculation
    # raises there again. The trace shows a node with no value for it.
    sim = core_toy_simulation(
        core_leaf, core_raises, core_catches_a_failed_read, core_catches_its_own_month
    )
    assert sim.calculate(name, 2026) == 10
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(sim, name, 2026)

    assert contributions.to_dict() == {"core_leaf": 10}
    assert_unchanged(sim, before)


@pytest.mark.parametrize("year_first", [False, True])
def test_a_yearly_target_over_a_month(year_first):
    # Over a month it divides its year, so the recalculation has to calculate
    # the year again rather than divide the one the simulation holds.
    name = "core_leaf_and_double"
    sim = core_toy_simulation(core_leaf, core_double, core_leaf_and_double)
    if year_first:
        sim.calculate(name, 2026)
    assert sim.calculate(name, "2026-03") == 2.5
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(sim, name, "2026-03")

    assert contributions.to_dict() == pytest.approx(
        {"core_double": 20 / 12, "core_leaf": 10 / 12}
    )
    assert_unchanged(sim, before)


def test_household_net_income_over_a_month():
    sim = traced_simulation(2026, [(40, 40_000.0, 0.0)], [])
    mean = sim.calculate("household_net_income", "2026-03").mean()
    assert mean > 0

    contributions = calculate_dependency_contributions(
        sim, "household_net_income", "2026-03"
    )

    assert contributions.sum() == pytest.approx(mean, abs=tolerance(mean))


class bus_in_london_trips(CoreVariable):
    # A name utils/supplied_inputs.py answers for, with a calculation that
    # gives the NaN set_input refuses.
    label = "Calculated NaN"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return np.nan


def leaf_unless_supplied(person, on, period):
    on("bus_in_london_trips", period)
    supplied = supplied_input(on, "bus_in_london_trips", period) is not None
    stored = stored_as_input(on, "bus_in_london_trips", period)
    return on("core_leaf", period) + 100 * supplied + 1000 * stored


class core_asks_about_nan(CoreVariable):
    label = "Core asks about NaN"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        return leaf_unless_supplied(person, person, period)


class core_asks_about_nan_on_a_branch(CoreVariable):
    label = "Core asks about NaN on a branch"
    value_type = float
    entity = CORE_PERSON
    definition_period = YEAR

    def formula(person, period):
        sim = person.simulation
        route = sim.get_branch("nan_route")
        try:
            return leaf_unless_supplied(person, route.populations["person"], period)
        finally:
            del sim.branches["nan_route"]


@pytest.mark.parametrize(
    "target,cache_blacklist",
    [
        # The simulation doesn't store the NaN, so the branch holds it.
        (core_asks_about_nan, ["bus_in_london_trips"]),
        # The formula read it on a branch that's gone, so the branch holds it.
        (core_asks_about_nan_on_a_branch, None),
    ],
)
def test_a_calculated_nan_stays_calculated(target, cache_blacklist):
    sim = core_toy_simulation(
        bus_in_london_trips, core_leaf, target, cache_blacklist=cache_blacklist
    )
    assert sim.calculate(target.__name__, 2026) == 10
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(sim, target.__name__, 2026)

    assert contributions.to_dict() == {"core_leaf": 10, "bus_in_london_trips": 0}
    assert_unchanged(sim, before)


# NaN, each infinity and any finite float32: arrays()'s own float elements
# rarely give NaN.
ELEMENTS = st.one_of(
    st.just(float("nan")),
    st.just(float("inf")),
    st.just(float("-inf")),
    st.floats(width=32, allow_nan=False, allow_infinity=False),
)


def float32_arrays(length):
    return arrays(np.float32, length, elements=ELEMENTS, fill=st.nothing())


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(values=float32_arrays(1))
@example(values=np.array([np.nan], dtype=np.float32))
def test_a_recorded_value_stays_what_it_was_recorded_as(values):
    name = "bus_in_london_trips"
    year = periods.period(2026)
    sim = core_toy_simulation(bus_in_london_trips)
    person = sim.populations["person"]
    sim.get_holder(name)._set(year, values, sim.branch_name, is_input=True)
    record_model_value(sim, name, year, sim.branch_name, calculated=True)
    assert supplied_input(person, name, year) is None
    assert not stored_as_input(person, name, year)
    record_model_value(sim, name, year, sim.branch_name)
    assert supplied_input(person, name, year) is None
    assert stored_as_input(person, name, year)


@settings(max_examples=200, deadline=None)
@given(
    a=float32_arrays(3),
    b=float32_arrays(3),
    # Elements where this holds match a's, so that arrays that agree come up.
    matching=arrays(np.bool_, 3),
)
@example(
    a=np.full(3, np.nan, np.float32),
    b=np.full(3, np.nan, np.float32),
    matching=np.zeros(3, np.bool_),
)
def test_same_array_is_equality_where_nan_equals_nan(a, b, matching):
    b = np.where(matching, a, b)
    expected = bool(np.all((a == b) | (np.isnan(a) & np.isnan(b))))
    assert same_array(a, b) == expected
    assert same_values(a, b) == expected
    # The aggregate impact tool's copy, for a base's package without same_array.
    assert _same_array(a, b) == expected
    assert same_array(a, a.view(CalculatedValue))


@pytest.mark.parametrize("compare", [same_array, _same_array])
def test_same_array_compares_what_cannot_hold_nan(compare):
    assert compare(np.array(["a", "b"]), np.array(["a", "b"]))
    assert not compare(np.array(["a", "b"]), np.array(["a", "c"]))
    assert not compare(np.array([1.0]), np.array([1.0, 2.0]))


def landlord(finance_costs):
    return {
        "property_rental_income": 2_000,
        "property_income": 2_000,
        "property_finance_costs": finance_costs,
    }


def test_a_read_on_a_subset_of_households_raises():
    # uses_property_allowance compares income tax with and without the
    # allowance on branches of a subset of households (household_subset). The
    # trace does not show which households the subset held, and zeroing a
    # dependency can change them, so nothing can hold the values it read there.
    # An employee, and the two landlords test_household_subset.py lists as
    # electing, each in a household of their own.
    year = 2026
    adults = [
        ({"age": 40, "employment_income": 30_000}, False),
        ({"age": 40, "employment_income": 30_000, **landlord(100)}, True),
        ({"age": 70, "private_pension_income": 33_500, **landlord(1_500)}, True),
    ]
    people, benunits, households = {}, {}, {}
    for i, (adult, claims_pension_credit) in enumerate(adults):
        person = f"adult_{i}"
        people[person] = {name: {year: value} for name, value in adult.items()}
        benunits[f"benunit_{i}"] = {
            "members": [person],
            "would_claim_pc": {year: claims_pension_credit},
            "would_claim_uc": {year: False},
        }
        households[f"household_{i}"] = {
            "members": [person],
            "country": {year: "ENGLAND"},
        }
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households},
        trace=True,
    )
    assert sim.calculate("uses_property_allowance", year).tolist() == [
        False,
        True,
        True,
    ]
    before = snapshot(sim)

    with pytest.raises(ValueError, match="subset of households"):
        calculate_dependency_contributions(
            sim, "uses_property_allowance", year, map_to="household"
        )
    assert_unchanged(sim, before)


def test_reads_a_formula_asks_were_supplied_stay_as_they_were():
    # person_bus_fare_spending splits local_bus_trips by region unless the
    # situation supplied bus_in_london_trips or other_local_bus_trips, which
    # it asks supplied_input. This one supplied neither: the formula read both
    # as zero, and zeroing them leaves supplied_input's answer, and so the
    # spending, as it was.
    year = 2026
    sim = Simulation(
        situation={
            "people": {"person": {"age": {year: 40}, "local_bus_trips": {year: 100}}},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {
                "household": {"members": ["person"], "region": {year: "NORTH_EAST"}}
            },
        },
        trace=True,
    )
    spending = sim.calculate("person_bus_fare_spending", year)[0]
    assert spending > 0
    trips = ["bus_in_london_trips", "other_local_bus_trips"]
    for name in trips:
        assert sim.calculate(name, year).tolist() == [0]
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(
        sim, "person_bus_fare_spending", year
    )

    for name in trips:
        assert contributions[name] == 0
    # With no local bus trips, the person spends nothing.
    assert contributions["local_bus_trips"] == pytest.approx(
        spending, abs=tolerance(spending)
    )
    assert_unchanged(sim, before)


def test_housing_benefit_reads_its_applicable_income_as_calculated():
    # 2026 has two accommodation-disregard periods (from 5 October). Then
    # housing_benefit_entitlement uses the applicable income it read only
    # where pension-age rules or a passporting benefit keep annual income,
    # unless a scenario set the income as an input (stored_as_input), when the
    # award comes from it alone. Neither rule applies here, and the simulation
    # calculated the income, so zeroing it leaves the award as it was. As an
    # input, the zero would raise the award to the full rent.
    year = 2026
    income = "housing_benefit_applicable_income"
    sim = Simulation(situation=housing_benefit_situation((year,)), trace=True)
    entitlement = sim.calculate("housing_benefit_entitlement", year)[0]
    assert 0 < entitlement < 10_400
    assert sim.calculate(income, year)[0] > 0
    benunit = sim.populations["benunit"]
    assert not stored_as_input(benunit, income, periods.period(year))
    before = snapshot(sim)

    contributions = calculate_dependency_contributions(
        sim, "housing_benefit_entitlement", year
    )

    assert contributions[income] == 0
    assert_unchanged(sim, before)
    supplied = Simulation(situation=housing_benefit_situation((year,)))
    supplied.set_input(income, year, [0.0])
    assert supplied.calculate("housing_benefit_entitlement", year)[0] == pytest.approx(
        10_400
    )
