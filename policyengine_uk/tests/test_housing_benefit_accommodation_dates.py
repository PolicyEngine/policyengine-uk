"""Statutory dates and reform compatibility for HB accommodation disregards."""

from datetime import date

import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_core.periods import period

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.model_api import Variable, BenUnit, YEAR
from policyengine_uk.utils.aggregate_impact.guard import snapshot_inputs
from policyengine_uk.utils.supplied_inputs import (
    set_model_value,
    stored_as_input,
    supplied_input,
)


PREFIX = (
    "gov.dwp.housing_benefit.means_test.income_disregard."
    "specified_or_temporary_accommodation"
)


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def node(parameters):
    return parameters.gov.dwp.housing_benefit.means_test.income_disregard.specified_or_temporary_accommodation


@pytest.mark.parametrize(
    "family,age,amount",
    [
        ("single", "younger", 61.41),
        ("single", "older", 77.73),
        ("lone_parent", "younger", 61.41),
        ("lone_parent", "older", 77.73),
        ("couple", "minors", 97.33),
        ("couple", "younger", 61.53),
        ("couple", "older", 119.70),
    ],
)
def test_processed_amounts_keep_5_october_commencement(system, family, age, amount):
    """GB SI 2026/753 and NI SR 2026/157 commence on 5 October, not January."""
    leaf = node(system.parameters).children[family].children[age]
    assert leaf("2026-10-04") == 0
    assert leaf("2026-10-05") == amount


def situation(years=(2026,)):
    return {
        "people": {
            "person1": {
                "age": {year: 30 for year in years},
                "employment_income": {year: 1_000 for year in years},
                "income_tax": {year: 0 for year in years},
                "national_insurance": {year: 0 for year in years},
                "pension_contributions": {year: 0 for year in years},
            }
        },
        "benunits": {
            "family": {
                "members": ["person1"],
                "in_specified_or_temporary_accommodation": {
                    year: True for year in years
                },
                "housing_benefit_net_earnings": {year: 1_000 for year in years},
                "housing_benefit_special_earnings_disregard": {
                    year: 260 for year in years
                },
                "housing_benefit_applicable_amount": {year: 500 for year in years},
                "housing_benefit_on_passporting_benefit": {
                    year: False for year in years
                },
                "housing_benefit_pension_age_regulations_apply": {
                    year: False for year in years
                },
                "housing_benefit_tariff_income": {year: 0 for year in years},
                "housing_benefit_applicable_income_childcare_element": {
                    year: 0 for year in years
                },
                "meets_housing_benefit_additional_earnings_disregard_conditions": {
                    year: False for year in years
                },
                "benunit_rent": {year: 10_400 for year in years},
                "housing_benefit_meals_deduction": {year: 0 for year in years},
                "housing_benefit_non_dep_deductions": {year: 0 for year in years},
                "LHA_eligible": {year: False for year in years},
                "income_support": {year: 0 for year in years},
                "jsa_income": {year: 0 for year in years},
                "esa_income": {year: 0 for year in years},
                "tax_credits": {year: 0 for year in years},
            }
        },
        "households": {"household": {"members": ["person1"]}},
    }


def test_first_year_combines_completed_awards():
    """Reg 71: average the awards, not the income before its £500 threshold."""
    simulation = Simulation(situation=situation())
    before = 10_400 - 0.65 * (1_000 - 260 - 500)
    after = 10_400
    days_before = (date(2026, 10, 5) - date(2026, 4, 6)).days
    days_after = (date(2027, 4, 6) - date(2026, 10, 5)).days
    expected = (before * days_before + after * days_after) / 365
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(expected, abs=0.01)


def test_bare_year_zero_reform_has_fiscal_year_boundaries():
    """A 2026 reform must not leak into the following 2027-28 fiscal year."""
    simulation = Simulation(
        situation=situation((2025, 2026, 2027)),
        reform={f"{PREFIX}.single.older": {"2026": 0}},
    )
    amounts = [
        simulation.calculate(
            "housing_benefit_specified_or_temporary_accommodation_disregard", year
        )[0]
        for year in (2025, 2026, 2027)
    ]
    assert amounts == pytest.approx([0, 0, 77.73 * 52], abs=0.01)


def test_dated_zero_reform_is_not_overwritten():
    simulation = Simulation(
        situation=situation(),
        reform={f"{PREFIX}.single.older": {"2026-10-05.2027-04-05": 0}},
    )
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(10_400 - 0.65 * (1_000 - 260 - 500), abs=0.01)


def test_later_supplied_income_keeps_its_value():
    simulation = Simulation(situation=situation())
    simulation.set_input("housing_benefit_applicable_income", 2026, [2_000])
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(10_400 - 0.65 * (2_000 - 500), abs=0.01)


def test_single_day_zero_reform_changes_only_that_day():
    simulation = Simulation(
        situation=situation(),
        reform={f"{PREFIX}.single.older": {"2026-10-05": 0}},
    )
    before = 10_400 - 0.65 * (1_000 - 260 - 500)
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx((before * 183 + 10_400 * 182) / 365, abs=0.01)


def test_only_supplied_period_overrides_recalculation():
    data = situation((2025, 2026))
    data["benunits"]["family"]["housing_benefit_applicable_income"] = {2025: 2_000}
    simulation = Simulation(situation=data)
    before = 10_400 - 0.65 * (1_000 - 260 - 500)
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx((before * 182 + 10_400 * 183) / 365, abs=0.01)


def test_rebuilt_populations_leave_no_supplied_income_behind():
    data = situation()
    data["benunits"]["family"]["housing_benefit_applicable_income"] = {2026: 2_000}
    simulation = Simulation(situation=data)
    simulation.build_from_populations(Simulation(situation=situation()).populations)
    simulation.calculate("housing_benefit_applicable_income", 2026)
    before = 10_400 - 0.65 * (1_000 - 260 - 500)
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx((before * 182 + 10_400 * 183) / 365, abs=0.01)


@pytest.mark.parametrize(
    "variable",
    [
        "housing_benefit_applicable_income",
        "housing_benefit_applicable_income_disregard",
        "housing_benefit_specified_or_temporary_accommodation_disregard",
    ],
)
def test_rebuilt_populations_keep_a_calculated_value_calculated(variable):
    # The populations come from a simulation that has calculated the value;
    # this simulation's own record still says it was supplied.
    data = situation()
    data["benunits"]["family"][variable] = {2026: 2_000}
    simulation = Simulation(situation=data)
    donor = Simulation(situation=situation())
    donor.calculate(variable, 2026)
    simulation.build_from_populations(donor.populations)
    before = 10_400 - 0.65 * (1_000 - 260 - 500)
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx((before * 182 + 10_400 * 183) / 365, abs=0.01)


def test_rebuilt_populations_keep_a_supplied_income():
    data = situation()
    data["benunits"]["family"]["housing_benefit_applicable_income"] = {2026: 3_000}
    simulation = Simulation(situation=situation())
    simulation.build_from_populations(Simulation(situation=data).populations)
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(10_400 - 0.65 * (3_000 - 500), abs=0.01)


def test_scenario_adjusted_income_keeps_its_value():
    simulation = Simulation(situation=situation())
    set_model_value(simulation, "housing_benefit_applicable_income", 2026, [2_000])
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(10_400 - 0.65 * (2_000 - 500), abs=0.01)


def snapshotted(simulation):
    # The aggregate-impact guard discards formula results before it captures
    # the inputs, so it must tell them apart from rebuilt populations' inputs.
    snapshot_inputs(simulation, ["housing_benefit_applicable_income"])
    return simulation


# A clone or branch copies its simulation's records and binds the holders it
# copies to itself, so it must find the records of rebuilt populations there.
REBUILT_AND_COPIES = pytest.mark.parametrize(
    "copy",
    [
        lambda simulation: simulation,
        lambda simulation: simulation.clone(),
        lambda simulation: simulation.get_branch("after_rebuild"),
        snapshotted,
    ],
    ids=["rebuilt", "clone", "branch", "snapshot"],
)


@REBUILT_AND_COPIES
def test_copies_of_rebuilt_populations_keep_a_supplied_income(copy):
    data = situation()
    data["benunits"]["family"]["housing_benefit_applicable_income"] = {2026: 3_000}
    simulation = Simulation(situation=situation())
    simulation.build_from_populations(Simulation(situation=data).populations)
    copied = copy(simulation)
    assert copied.calculate("housing_benefit_entitlement", 2026)[0] == pytest.approx(
        10_400 - 0.65 * (3_000 - 500), abs=0.01
    )
    benunit = copied.populations["benunit"]
    assert supplied_input(
        benunit, "housing_benefit_applicable_income", period(2026)
    ).tolist() == [3_000]


@REBUILT_AND_COPIES
def test_copies_of_rebuilt_populations_keep_a_calculated_income_calculated(copy):
    data = situation()
    data["benunits"]["family"]["housing_benefit_applicable_income"] = {2026: 2_000}
    simulation = Simulation(situation=data)
    donor = Simulation(situation=situation())
    donor.calculate("housing_benefit_applicable_income", 2026)
    simulation.build_from_populations(donor.populations)
    copied = copy(simulation)
    before = 10_400 - 0.65 * (1_000 - 260 - 500)
    assert copied.calculate("housing_benefit_entitlement", 2026)[0] == pytest.approx(
        (before * 182 + 10_400 * 183) / 365, abs=0.01
    )
    benunit = copied.populations["benunit"]
    assert (
        supplied_input(benunit, "housing_benefit_applicable_income", period(2026))
        is None
    )


@REBUILT_AND_COPIES
def test_copies_of_rebuilt_populations_keep_a_scenario_adjusted_income(copy):
    donor = Simulation(situation=situation())
    set_model_value(donor, "housing_benefit_applicable_income", 2026, [2_000])
    simulation = Simulation(situation=situation())
    simulation.build_from_populations(donor.populations)
    copied = copy(simulation)
    assert copied.calculate("housing_benefit_entitlement", 2026)[0] == pytest.approx(
        10_400 - 0.65 * (2_000 - 500), abs=0.01
    )
    # Still the model's value, not a supplied one.
    benunit = copied.populations["benunit"]
    assert (
        supplied_input(benunit, "housing_benefit_applicable_income", period(2026))
        is None
    )


def test_simulations_rebuilt_from_the_same_populations_answer_alone():
    data = situation()
    data["benunits"]["family"]["housing_benefit_applicable_income"] = {2026: 3_000}
    donor = Simulation(situation=data)
    first = Simulation(situation=situation())
    second = Simulation(situation=situation())
    first.build_from_populations(donor.populations)
    second.build_from_populations(donor.populations)
    award = pytest.approx(10_400 - 0.65 * (3_000 - 500), abs=0.01)
    assert second.calculate("housing_benefit_entitlement", 2026)[0] == award
    first.set_input("housing_benefit_applicable_income", 2026, [4_000])
    assert first.calculate("housing_benefit_entitlement", 2026)[0] == pytest.approx(
        10_400 - 0.65 * (4_000 - 500), abs=0.01
    )
    assert second.calculate("housing_benefit_entitlement", 2026)[0] == award
    assert donor.calculate("housing_benefit_entitlement", 2026)[0] == award


def test_rebuilt_populations_replace_values_calculated_before():
    # Formulas read the fast cache, which held the income calculated here.
    simulation = Simulation(situation=situation())
    simulation.calculate("housing_benefit_applicable_income", 2026)
    data = situation()
    data["benunits"]["family"]["housing_benefit_applicable_income"] = {2026: 3_000}
    simulation.build_from_populations(Simulation(situation=data).populations)
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(10_400 - 0.65 * (3_000 - 500), abs=0.01)


# How a simulation comes to hold each override variable's 2026 value.
OVERRIDE_VARIABLES = (
    "housing_benefit_applicable_income",
    "housing_benefit_applicable_income_disregard",
    "housing_benefit_specified_or_temporary_accommodation_disregard",
)
SIMULATION_STATES = st.tuples(
    *(
        st.tuples(
            st.sampled_from(["absent", "supplied", "model", "calculated"]),
            st.integers(0, 4_000),
        )
        for _ in OVERRIDE_VARIABLES
    )
)


def simulation_in(state):
    data = situation()
    for name, (origin, amount) in zip(OVERRIDE_VARIABLES, state):
        if origin == "supplied":
            data["benunits"]["family"][name] = {2026: amount}
    simulation = Simulation(situation=data)
    for name, (origin, amount) in zip(OVERRIDE_VARIABLES, state):
        if origin == "model":
            set_model_value(simulation, name, 2026, [amount])
        elif origin == "calculated":
            simulation.calculate(name, 2026)
    return simulation


def provenance_and_award(simulation):
    benunit = simulation.populations["benunit"]
    provenance = []
    for name in OVERRIDE_VARIABLES:
        supplied = supplied_input(benunit, name, period(2026))
        provenance.append(
            (
                stored_as_input(benunit, name, period(2026)),
                None if supplied is None else supplied.tolist(),
            )
        )
    award = simulation.calculate("housing_benefit_entitlement", 2026).tolist()
    return provenance, award


@settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(donor_state=SIMULATION_STATES, receiver_state=SIMULATION_STATES)
# The other simulation cached income before a scenario set its disregard.
@example(
    donor_state=(("calculated", 868), ("model", 0), ("supplied", 0)),
    receiver_state=(("absent", 0),) * 3,
)
# This simulation calculated income before taking supplied income.
@example(
    donor_state=(("supplied", 2_589), ("absent", 0), ("absent", 0)),
    receiver_state=(("calculated", 0), ("absent", 0), ("absent", 0)),
)
def test_rebuilt_populations_answer_as_the_simulation_that_made_them(
    donor_state, receiver_state
):
    """R1: for the states generated here (each override variable absent,
    supplied, set by a scenario or calculated for 2026, on the default
    branch), whichever of them this simulation held before, populations taken
    from another simulation give the provenance and award of a fresh copy of
    that simulation, in this simulation and in its clones and branches."""
    expected = provenance_and_award(simulation_in(donor_state))
    simulation = simulation_in(receiver_state)
    simulation.build_from_populations(simulation_in(donor_state).populations)
    copies = [simulation, simulation.clone(), simulation.get_branch("after_rebuild")]
    for copied in copies:
        assert provenance_and_award(copied) == expected


def test_replaced_income_formula_is_not_bypassed():
    class housing_benefit_applicable_income(Variable):
        entity = BenUnit
        definition_period = YEAR
        value_type = float

        def formula(benunit, period, parameters):
            return benunit.filled_array(2_000)

    simulation = Simulation(situation=situation())
    simulation.tax_benefit_system.update_variable(housing_benefit_applicable_income)
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(10_400 - 0.65 * (2_000 - 500), abs=0.01)


def test_neutralized_income_is_not_recalculated():
    simulation = Simulation(situation=situation())
    simulation.tax_benefit_system.neutralize_variable(
        "housing_benefit_applicable_income"
    )
    assert simulation.calculate("housing_benefit_entitlement", 2026)[0] == 10_400


def test_replaced_disregard_formula_is_not_bypassed():
    class housing_benefit_applicable_income_disregard(Variable):
        entity = BenUnit
        definition_period = YEAR
        value_type = float

        def formula(benunit, period, parameters):
            return benunit.filled_array(100)

    simulation = Simulation(situation=situation())
    simulation.tax_benefit_system.update_variable(
        housing_benefit_applicable_income_disregard
    )
    assert simulation.calculate("housing_benefit_entitlement", 2026)[
        0
    ] == pytest.approx(10_400 - 0.65 * (1_000 - 100 - 500), abs=0.01)


def test_calculation_does_not_reparent_or_edit_parameter_leaves():
    simulation = Simulation(situation=situation())
    schedule = node(simulation.tax_benefit_system.parameters)
    parents = {
        leaf.name: leaf.parent
        for family in ("single", "lone_parent", "couple")
        for leaf in schedule.children[family].children.values()
    }
    values = {
        leaf.name: [(value.instant_str, value.value) for value in leaf.values_list]
        for family in ("single", "lone_parent", "couple")
        for leaf in schedule.children[family].children.values()
    }
    simulation.calculate("housing_benefit_entitlement", 2026)
    for family in ("single", "lone_parent", "couple"):
        for leaf in schedule.children[family].children.values():
            assert leaf.parent is parents[leaf.name]
            assert [
                (value.instant_str, value.value) for value in leaf.values_list
            ] == values[leaf.name]
