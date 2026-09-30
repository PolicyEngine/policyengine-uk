"""Every reform representation works through ``Simulation(reform=...)``.

``Scenario.from_reform`` used to instantiate a Reform class with no
arguments, but policyengine-core's ``Reform.__init__`` takes the baseline
tax-benefit system, so every structural Reform class (and every tuple
containing one) raised ``TypeError`` before a simulation was built. A
simulation applies a Reform class to its own system, as
``Simulation.apply_reform`` does, rather than instantiating it.

Invariants, for every reform representation R:

1. Baseline invariance: ``Simulation(reform=R).baseline`` gives the same
   results as a simulation built with no reform.
2. Representation equivalence (differential): a parameter dict with
   ``start.stop`` keys, the same dict as a ``Reform.from_dict`` class, a
   ``Reform`` subclass making the same update (directly or through
   ``modify_parameters`` / ``set_parameter``), a ``Reform`` instance, and a
   one-element tuple of any of these all give identical results.
3. Composition: ``reform=(A, B)`` equals applying A and then B with
   ``Simulation.apply_reform``; ``reform=()`` is no reform; nested tuples
   flatten in order.
4. Timing: a Reform class in a Scenario with ``applied_before_data_load``
   behaves as the same change given as a dict, including activating a
   parameter-gated structural reform.
5. Isolation: a reform changes only its own simulation, never the
   module-level system or a simulation built afterwards.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode
from policyengine_core.periods import instant
from policyengine_core.periods import period as period_
from policyengine_core.reforms import Reform, set_parameter

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.model_api import YEAR, Person, Variable
from policyengine_uk.system import system
from policyengine_uk.utils.scenario import Scenario

YEAR_ = 2026
PERSONAL_ALLOWANCE = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
NO_PERSONAL_ALLOWANCE = {PERSONAL_ALLOWANCE: {f"{YEAR_}-01-01.{YEAR_}-12-31": 0}}
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)


def situation(*incomes):
    people = {
        f"p{i}": {"age": {YEAR_: 40}, "employment_income": {YEAR_: income}}
        for i, income in enumerate(incomes)
    }
    return {
        "people": people,
        "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(len(incomes))},
        "households": {f"h{i}": {"members": [f"p{i}"]} for i in range(len(incomes))},
    }


SITUATION = situation(50_000)


def tax(simulation, year=YEAR_):
    return np.asarray(simulation.calculate("income_tax", year), dtype=float)


class neutralize_income_tax(Reform):
    def apply(self):
        self.neutralize_variable("income_tax")


class income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax (test override)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("employment_income", period) * 0 + 1_234


class flat_income_tax(Reform):
    def apply(self):
        self.update_variable(income_tax)


def _no_personal_allowance(parameters):
    parameters.get_child(PERSONAL_ALLOWANCE).update(
        period=period_(f"year:{YEAR_}:1"), value=0
    )
    return parameters


class no_personal_allowance_via_modify_parameters(Reform):
    def apply(self):
        self.modify_parameters(_no_personal_allowance)


class no_personal_allowance_via_direct_update(Reform):
    def apply(self):
        self.parameters.get_child(PERSONAL_ALLOWANCE).update(
            period=period_(f"year:{YEAR_}:1"), value=0
        )


class test_bonus(Variable):
    value_type = float
    entity = Person
    label = "Test bonus read from a parameter the reform adds"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) * 0 + parameters(period).test_reform.bonus


class add_parameter_and_variable(Reform):
    def apply(self):
        self.parameters.add_child(
            "test_reform",
            ParameterNode(
                "test_reform", data={"bonus": {"values": {"2000-01-01": 777}}}
            ),
        )
        self.add_variable(test_bonus)


@pytest.fixture(scope="module")
def baseline_income_tax():
    return tax(Simulation(situation=SITUATION))


def test_reform_class_no_longer_raises_type_error():
    Simulation(situation=SITUATION, reform=neutralize_income_tax)


def test_neutralizing_reform_class(baseline_income_tax):
    simulation = Simulation(situation=SITUATION, reform=neutralize_income_tax)
    assert baseline_income_tax[0] > 0
    assert tax(simulation)[0] == 0
    np.testing.assert_array_equal(tax(simulation.baseline), baseline_income_tax)


def test_formula_replacing_reform_class(baseline_income_tax):
    simulation = Simulation(situation=SITUATION, reform=flat_income_tax)
    assert tax(simulation)[0] == 1_234
    np.testing.assert_array_equal(tax(simulation.baseline), baseline_income_tax)


@pytest.mark.parametrize(
    "reform",
    [
        pytest.param(
            no_personal_allowance_via_modify_parameters, id="modify_parameters"
        ),
        pytest.param(no_personal_allowance_via_direct_update, id="direct_update"),
        pytest.param(Reform.from_dict(NO_PERSONAL_ALLOWANCE), id="Reform.from_dict"),
        pytest.param(
            set_parameter(PERSONAL_ALLOWANCE, 0, period=f"year:{YEAR_}:1"),
            id="set_parameter",
        ),
        pytest.param(no_personal_allowance_via_direct_update(system), id="instance"),
        pytest.param((no_personal_allowance_via_direct_update,), id="one_tuple"),
        pytest.param((NO_PERSONAL_ALLOWANCE,), id="one_tuple_dict"),
        pytest.param(((NO_PERSONAL_ALLOWANCE,),), id="nested_tuple_dict"),
    ],
)
def test_parametric_reform_representations_match_the_dict(reform, baseline_income_tax):
    from_dict = tax(Simulation(situation=SITUATION, reform=NO_PERSONAL_ALLOWANCE))
    simulation = Simulation(situation=SITUATION, reform=reform)
    assert from_dict[0] > baseline_income_tax[0]
    np.testing.assert_array_equal(tax(simulation), from_dict)
    np.testing.assert_array_equal(tax(simulation.baseline), baseline_income_tax)


def test_reform_adding_a_parameter_node_and_variable():
    # The root at-instant cache for the default input year is populated while
    # the simulation is built, so the reform must reset parameter caches.
    simulation = Simulation(situation=SITUATION, reform=add_parameter_and_variable)
    assert simulation.calculate("test_bonus", 2025)[0] == 777
    assert simulation.calculate("test_bonus", YEAR_)[0] == 777
    assert "test_bonus" not in simulation.baseline.tax_benefit_system.variables


@pytest.mark.parametrize(
    "reforms, expected",
    [
        ((flat_income_tax, neutralize_income_tax), 0),
        ((neutralize_income_tax, flat_income_tax), 1_234),
        ((NO_PERSONAL_ALLOWANCE, neutralize_income_tax), 0),
        ((neutralize_income_tax, (flat_income_tax,)), 1_234),
    ],
)
def test_tuple_applies_reforms_in_order(reforms, expected):
    via_tuple = Simulation(situation=SITUATION, reform=reforms)
    assert tax(via_tuple)[0] == expected

    sequential = Simulation(situation=SITUATION)

    def flatten(items):
        for item in items:
            if isinstance(item, tuple):
                yield from flatten(item)
            else:
                yield item

    for reform in flatten(reforms):
        sequential.apply_reform(reform)
    np.testing.assert_array_equal(tax(via_tuple), tax(sequential))


def test_empty_tuple_is_no_reform(baseline_income_tax):
    simulation = Simulation(situation=SITUATION, reform=())
    np.testing.assert_array_equal(tax(simulation), baseline_income_tax)


@pytest.mark.parametrize(
    "reform",
    [
        pytest.param(42, id="int"),
        pytest.param((neutralize_income_tax, system), id="legacy_class_with_args"),
    ],
)
def test_unsupported_reform_types_raise_value_error(reform):
    with pytest.raises(ValueError, match="Unsupported reform type"):
        Simulation(situation=SITUATION, reform=reform)


def _tiny_dataset():
    person = pd.DataFrame(
        {
            "person_id": [1, 2],
            "person_benunit_id": [1, 2],
            "person_household_id": [1, 2],
            "age": [40, 35],
            "employment_income": [50_000.0, 20_000.0],
            "person_weight": [1.0, 1.0],
        }
    )
    benunit = pd.DataFrame({"benunit_id": [1, 2], "benunit_weight": [1.0, 1.0]})
    household = pd.DataFrame(
        {
            "household_id": [1, 2],
            "household_weight": [1.0, 1.0],
            "region": ["LONDON", "NORTH_EAST"],
            "tenure_type": ["OWNED_OUTRIGHT", "OWNED_OUTRIGHT"],
            "council_tax": [1_500.0, 1_200.0],
            "rent": [0.0, 0.0],
        }
    )
    return UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=2025
    )


@pytest.mark.parametrize(
    "reform",
    [
        pytest.param(neutralize_income_tax, id="neutralize"),
        pytest.param(Reform.from_dict(NO_PERSONAL_ALLOWANCE), id="Reform.from_dict"),
        pytest.param(
            (NO_PERSONAL_ALLOWANCE, no_personal_allowance_via_direct_update),
            id="tuple",
        ),
    ],
)
def test_microsimulation_accepts_reform_classes(reform):
    baseline = tax(Microsimulation(dataset=_tiny_dataset()))
    microsimulation = Microsimulation(dataset=_tiny_dataset(), reform=reform)
    if reform is neutralize_income_tax:
        expected = np.zeros_like(baseline)
    else:
        expected = tax(
            Microsimulation(dataset=_tiny_dataset(), reform=NO_PERSONAL_ALLOWANCE)
        )
    np.testing.assert_array_equal(tax(microsimulation), expected)
    assert not np.array_equal(expected, baseline)
    np.testing.assert_array_equal(tax(microsimulation.baseline), baseline)


MARRIED_ONE_EARNER = {
    "people": {
        "earner": {"age": {YEAR_: 40}, "employment_income": {YEAR_: 80_000}},
        "partner": {"age": {YEAR_: 40}, "employment_income": {YEAR_: 0}},
    },
    "benunits": {
        "benunit": {"members": ["earner", "partner"], "is_married": {YEAR_: True}}
    },
    "households": {"household": {"members": ["earner", "partner"]}},
}
# Gates a structural reform built from parameters during Simulation.__init__
# (sampled at the default input period, so the change must cover 2025).
REMOVE_MA_INCOME_CONDITION = {
    "gov.contrib.cps.marriage_tax_reforms.expanded_ma.remove_income_condition": {
        "2025-01-01.2030-12-31": True
    }
}


@pytest.mark.parametrize("applied_before_data_load", [False, True])
def test_reform_class_timing_matches_the_dict(applied_before_data_load):
    def marriage_allowance(reform):
        scenario = Scenario.from_reform(reform)
        scenario.applied_before_data_load = applied_before_data_load
        simulation = Simulation(situation=MARRIED_ONE_EARNER, scenario=scenario)
        return simulation.calculate("marriage_allowance", YEAR_)[0]

    as_dict = marriage_allowance(REMOVE_MA_INCOME_CONDITION)
    as_class = marriage_allowance(Reform.from_dict(REMOVE_MA_INCOME_CONDITION))
    assert as_class == as_dict
    if applied_before_data_load:
        assert as_class > 0


def test_reform_class_applied_before_data_load_neutralizes(baseline_income_tax):
    scenario = Scenario.from_reform(neutralize_income_tax)
    scenario.applied_before_data_load = True
    simulation = Simulation(situation=SITUATION, scenario=scenario)
    assert tax(simulation)[0] == 0
    np.testing.assert_array_equal(tax(simulation.baseline), baseline_income_tax)


def test_reforms_do_not_leak_into_other_simulations():
    before = tax(Simulation(situation=SITUATION))
    for reform in (
        neutralize_income_tax,
        flat_income_tax,
        no_personal_allowance_via_modify_parameters,
        no_personal_allowance_via_direct_update,
        Reform.from_dict(NO_PERSONAL_ALLOWANCE),
        add_parameter_and_variable,
    ):
        Simulation(situation=SITUATION, reform=reform)
    after = Simulation(situation=SITUATION)
    np.testing.assert_array_equal(tax(after), before)
    for tax_benefit_system in (after.tax_benefit_system, system):
        assert "test_bonus" not in tax_benefit_system.variables
        assert "test_reform" not in tax_benefit_system.parameters.children


@PROPERTY_SETTINGS
@given(
    allowance=st.integers(min_value=0, max_value=30_000),
    incomes=st.lists(
        st.integers(min_value=0, max_value=200_000), min_size=1, max_size=4
    ),
)
def test_parametric_reform_representations_agree(allowance, incomes):
    change = {PERSONAL_ALLOWANCE: {f"{YEAR_}-01-01.{YEAR_}-12-31": allowance}}

    class direct_update(Reform):
        def apply(self):
            self.parameters.get_child(PERSONAL_ALLOWANCE).update(
                start=instant(f"{YEAR_}-01-01"),
                stop=instant(f"{YEAR_}-12-31"),
                value=allowance,
            )

    case = situation(*incomes)
    unreformed = tax(Simulation(situation=case))
    results = []
    for reform in (change, Reform.from_dict(change), direct_update, (change,)):
        simulation = Simulation(situation=case, reform=reform)
        results.append(tax(simulation))
        np.testing.assert_array_equal(tax(simulation.baseline), unreformed)
    for result in results[1:]:
        np.testing.assert_array_equal(result, results[0])
