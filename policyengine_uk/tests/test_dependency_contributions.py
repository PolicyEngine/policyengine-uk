"""Tests for calculate_dependency_contributions in policyengine_uk.utils.dependencies.

The contribution of a variable the target reads directly (a direct dependency)
is the mean of the target minus the mean of the target recalculated over the
year with that dependency zero (over the year, and over any other period the
target read it) and every other variable the target read held at the value it
read, on the branch it read it. The trace shows which variables the target's
latest calculation over that year read, over which periods, on which branch,
and the values it read. A target that reads its own value within the year
raises, since recalculating it over the year replaces that value. For any
household drawn below:

1. Matches a reference: each float dependency's contribution equals the one
   from a fresh simulation in which the target's float direct dependencies are
   inputs at their calculated values, except the zeroed one. The reference
   uses no branches and deletes nothing.
2. Adds up: for a target defined only by `adds` and `subtracts` of its direct
   dependencies, the contributions sum to the mean of the target, also when
   one dependency feeds another (pension contributions get tax relief).
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
from policyengine_core.entities import build_entity
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
    Variable,
)
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
    # Each month is stored before the year is calculated, so the year's trace
    # node has a child for each month that only read the stored value; the
    # months' own calculations show what they read.
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
        # toy_annual would change it unless it is held.
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
    # A yearly variable read over a month: its year is zeroed.
    ("toy_annual_in_january", {"toy_annual": 100}),
    # A monthly flow summed over the year.
    ("toy_monthly_sum", {"toy_monthly": 78}),
    # A monthly stock read over a year: its last month.
    ("toy_stock_at_year", {"toy_stock": 12}),
    ("toy_eternal_at_year", {"toy_eternal": 77}),
    # toy_double reads toy_annual, but is held at 2,400 when toy_annual is
    # zeroed.
    ("toy_diamond", {"toy_annual": 1_200, "toy_double": 2_400}),
    # Last year's value (2,400), zeroed where it was read as well as over the
    # year, and held when toy_annual is zeroed.
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
    # year replaces, so that read cannot be held.
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


def core_toy_simulation(*variables, cache_blacklist=None):
    system = TaxBenefitSystem([CORE_PERSON])
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
    # core_double, read on the comparison branch too, is held there when
    # core_leaf is zeroed.
    assert calculate_dependency_contributions(
        sim, "core_sum_from_comparison", 2026
    ).to_dict() == {"core_leaf": 10, "core_double": 20}
    assert_unchanged(sim, before)


def test_an_uncached_read_is_held_at_the_value_it_read():
    # core_branch_sensitive is not stored, and recalculating it on another
    # branch gives 20: the trace shows the 10 the target read.
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
