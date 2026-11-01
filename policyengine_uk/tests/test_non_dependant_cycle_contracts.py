"""Universal Credit and Housing Benefit when the inputs supply cap totals.

Housing Benefit's non-dependant deductions read universal_credit, so no
baseline formula on Universal Credit's route may calculate Housing Benefit.
The Universal Credit cap counts Housing Benefit as nil (UC Regs 2013 reg
80(2A)): its basket, uc_benefit_cap_welfare_benefits, adds up the other
welfare benefits itself. Inputs that supply benefit_cap_welfare_benefits, a
total that includes Housing Benefit, also supply housing_benefit_pre_benefit_cap,
which the basket subtracts, or supply the basket itself.

The contract holds for every population: either the inputs leave
benefit_cap_welfare_benefits to the model, or they supply
housing_benefit_pre_benefit_cap or uc_benefit_cap_welfare_benefits beside it;
otherwise the basket raises ValueError, whether or not any household holds a
non-dependant. A value a scenario stores as the model's own (set_model_value)
supplies neither input. Under the contract, each household's Universal Credit
and Housing Benefit equal its results alone. A reform that makes Universal
Credit read calculated Housing Benefit adds a cycle, and the engine raises
CycleError.

The tests use two independent households: a single Universal Credit
claimant with £20,000 before a £14,753 cap and no rent; and a 70-year-old
paying £6,000 rent with a 40-year-old non-dependant who earns £9,000 at 20
hours and claims no Universal Credit. Alone, the first gets £14,753 of
Universal Credit. For the second's non-dependant the council deducts
£19.65 x 52 = £1,021.80 (HB Regs 2006 regs 70 and 74(2)(a), 2025-26),
leaving £4,978.20 of Housing Benefit.
"""

import copy

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.errors import CycleError
from policyengine_core.reforms import Reform
from policyengine_core.simulations import Simulation

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.utils.supplied_inputs import set_model_value
from policyengine_uk.variables.gov.dwp.benefit_cap_welfare_benefits import (
    benefit_cap_welfare_benefits as CombinedTotal,
)
from policyengine_uk.variables.gov.dwp.universal_credit.benefit_cap.uc_benefit_cap_welfare_benefits import (
    uc_benefit_cap_welfare_benefits as Basket,
)
from policyengine_uk.variables.gov.dwp.universal_credit.universal_credit_pre_benefit_cap import (
    universal_credit_pre_benefit_cap as PreCap,
)

YEAR = 2025
UC_MIXED = [14_753.0, 0.0, 0.0]
HB_MIXED = [0.0, 4_978.20, 0.0]
FIRST_REQUESTS = [
    "universal_credit",
    "housing_benefit",
    "housing_benefit_non_dep_deductions",
]
NO_AWARDS = dict(
    child_benefit=0.0,
    child_tax_credit=0.0,
    working_tax_credit=0.0,
    income_support=0.0,
    jsa_income=0.0,
    esa_income=0.0,
    pension_credit=0.0,
    uc_deductions=0.0,
    uc_deduction_rate=0.0,
    uc_childcare_element=0.0,
)


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def situation(which="mixed", year=YEAR, full_uc=False):
    """The claimant's household ("single"), the non-dependant's
    ("nondep"), or both ("mixed"), with no cap total supplied."""
    people, units, households = {}, {}, {}
    if which in ("single", "mixed"):
        people["uc"] = dict(
            age=40,
            current_education="NOT_IN_EDUCATION",
            employment_income=1_000.0,
            weekly_hours=20.0,
        )
        units["uc"] = dict(
            members=["uc"],
            **NO_AWARDS,
            would_claim_uc=True,
            uc_benefit_cap=14_753.0,
            benunit_is_rent_liable=False,
        )
        if not full_uc:
            units["uc"]["universal_credit_pre_benefit_cap"] = 20_000.0
        households["single"] = dict(
            members=["uc"],
            country="ENGLAND",
            local_authority="MAIDSTONE",
            rent=0.0,
            tenure_type="RENT_PRIVATELY",
        )
    if which in ("nondep", "mixed"):
        people["applicant"] = dict(age=70, current_education="NOT_IN_EDUCATION")
        people["nondep"] = dict(
            age=40,
            current_education="NOT_IN_EDUCATION",
            employment_income=9_000.0,
            weekly_hours=20.0,
        )
        for name in ["applicant", "nondep"]:
            units[name] = dict(
                members=[name],
                **NO_AWARDS,
                would_claim_uc=False,
                uc_benefit_cap=14_753.0,
                benunit_is_rent_liable=name == "applicant",
            )
            if not full_uc:
                units[name]["universal_credit_pre_benefit_cap"] = 0.0
        households["nondep"] = dict(
            members=["applicant", "nondep"],
            country="ENGLAND",
            local_authority="MAIDSTONE",
            rent=6_000.0,
            tenure_type="RENT_PRIVATELY",
        )
    return keyed(dict(people=people, benunits=units, households=households), year)


def keyed(data, year):
    """Key every input by year."""
    for entities in data.values():
        for entity in entities.values():
            for name, value in entity.items():
                if name != "members" and not isinstance(value, dict):
                    entity[name] = {year: value}
    return data


def supply(data, variable, values, year=YEAR):
    """Supply ``variable`` for every benefit unit, from ``values`` by unit
    name (nil for a unit it leaves out)."""
    for name, unit in data["benunits"].items():
        unit[variable] = {year: float(values.get(name, 0.0))}
    return data


def make(system, data, year=YEAR, trace=False):
    return Simulation(
        tax_benefit_system=system,
        situation=copy.deepcopy(data),
        default_input_period=year,
        default_calculation_period=year,
        trace=trace,
    )


def with_totals(which, **inputs):
    """The population with the combined total its Universal Credit and
    Housing Benefit imply supplied, and any other inputs."""
    data = situation(which)
    supply(data, "benefit_cap_welfare_benefits", {"uc": 20_000.0})
    for variable, values in inputs.items():
        supply(data, variable, values)
    return data


def traced_names(simulation):
    return {key.split("<")[0] for key in simulation.tracer.get_serialized_flat_trace()}


@pytest.mark.parametrize("first", FIRST_REQUESTS)
def test_a_supplied_universal_credit_basket_keeps_households_independent(system, first):
    """With the combined total and Universal Credit's basket supplied, each
    household gets its results alone, whatever the first request."""
    basket = {"uc": 20_000.0}
    alone = [
        make(system, with_totals(which, uc_benefit_cap_welfare_benefits=basket))
        for which in ["single", "nondep"]
    ]
    mixed = make(system, with_totals("mixed", uc_benefit_cap_welfare_benefits=basket))
    mixed.calculate(first, YEAR)
    for name, expected in [
        ("universal_credit", UC_MIXED),
        ("housing_benefit", HB_MIXED),
    ]:
        result = mixed.calculate(name, YEAR)
        np.testing.assert_allclose(result, expected, atol=0.01, err_msg=name)
        np.testing.assert_allclose(
            result,
            np.concatenate([sim.calculate(name, YEAR) for sim in alone]),
            atol=0.01,
            err_msg=name,
        )
    np.testing.assert_allclose(
        mixed.calculate("housing_benefit_non_dep_deductions", YEAR),
        [0.0, 1_021.80, 0.0],
        atol=0.01,
    )


@pytest.mark.parametrize("first", FIRST_REQUESTS)
def test_a_supplied_housing_benefit_gives_its_arithmetic(system, first):
    """With the combined total and Housing Benefit supplied, the basket is
    their difference, and Universal Credit and Housing Benefit follow from
    it. The claimant's total of £26,000 includes £6,000 of Housing Benefit
    (as in specified accommodation): the basket counts £20,000, £5,247 over
    the cap, so the award comes to £14,753, and HB reg 75F(1)(g) leaves the
    Housing Benefit uncapped. The applicant's total is their £4,978.20 of
    Housing Benefit, and pension age puts them outside the cap."""
    data = situation("mixed")
    supply(
        data,
        "benefit_cap_welfare_benefits",
        {"uc": 26_000.0, "applicant": 4_978.20},
    )
    supply(
        data,
        "housing_benefit_pre_benefit_cap",
        {"uc": 6_000.0, "applicant": 4_978.20},
    )
    sim = make(system, data)
    sim.calculate(first, YEAR)
    np.testing.assert_allclose(
        sim.calculate("uc_benefit_cap_welfare_benefits", YEAR),
        [20_000.0, 0.0, 0.0],
        atol=0.01,
    )
    np.testing.assert_allclose(
        sim.calculate("universal_credit", YEAR), UC_MIXED, atol=0.01
    )
    np.testing.assert_allclose(
        sim.calculate("housing_benefit", YEAR), [6_000.0, 4_978.20, 0.0], atol=0.01
    )
    # The deduction still reads the non-dependant's wages and Universal
    # Credit; the supplied Housing Benefit does not read the deduction.
    np.testing.assert_allclose(
        sim.calculate("housing_benefit_non_dep_deductions", YEAR),
        [0.0, 1_021.80, 0.0],
        atol=0.01,
    )


@pytest.mark.parametrize("which", ["mixed", "single"])
def test_a_supplied_total_alone_raises(system, which):
    """A supplied combined total without housing_benefit_pre_benefit_cap or
    uc_benefit_cap_welfare_benefits raises ValueError, with or without a
    non-dependant in the population, and the message names both inputs."""
    sim = make(system, with_totals(which))
    with pytest.raises(ValueError) as error:
        sim.calculate("universal_credit", YEAR)
    message = str(error.value)
    assert "housing_benefit_pre_benefit_cap" in message
    assert "uc_benefit_cap_welfare_benefits" in message
    assert "benefit_cap_welfare_benefits" in message


def test_a_reformed_total_leaves_universal_credit_on_its_basket(system):
    """A reform that gives benefit_cap_welfare_benefits a new formula changes
    the Housing Benefit cap's total, and Universal Credit's basket still adds
    up the benefits itself."""

    def formula(benunit, period, parameters):
        return CombinedTotal.formula(benunit, period, parameters) + 1_000

    class ReformedTotal(Reform):
        def apply(self):
            self.update_variable(
                type(
                    "benefit_cap_welfare_benefits",
                    (CombinedTotal,),
                    dict(formula=formula),
                )
            )

    baseline = make(system, situation("mixed"))
    reformed = make(ReformedTotal(system), situation("mixed"))
    np.testing.assert_allclose(
        reformed.calculate("benefit_cap_welfare_benefits", YEAR),
        baseline.calculate("benefit_cap_welfare_benefits", YEAR) + 1_000,
        atol=0.01,
    )
    for name in ["uc_benefit_cap_welfare_benefits", "universal_credit"]:
        np.testing.assert_allclose(
            reformed.calculate(name, YEAR),
            baseline.calculate(name, YEAR),
            atol=0.01,
            err_msg=name,
        )
    np.testing.assert_allclose(
        reformed.calculate("universal_credit", YEAR), UC_MIXED, atol=0.01
    )


def test_model_values_supply_neither_input(system):
    """set_model_value stores a value as the model's own, so it supplies
    neither the combined total nor Housing Benefit. A model value of the
    total leaves Universal Credit's basket adding up the benefits itself; a
    supplied total with a model value of Housing Benefit still raises."""
    baseline = make(system, situation("mixed"))
    basket = baseline.calculate("uc_benefit_cap_welfare_benefits", YEAR)
    stored_total = make(system, situation("mixed"))
    set_model_value(
        stored_total,
        "benefit_cap_welfare_benefits",
        YEAR,
        np.array([30_000.0, 0.0, 0.0]),
    )
    np.testing.assert_allclose(
        stored_total.calculate("uc_benefit_cap_welfare_benefits", YEAR),
        basket,
        atol=0.01,
    )
    np.testing.assert_allclose(
        stored_total.calculate("universal_credit", YEAR), UC_MIXED, atol=0.01
    )
    stored_housing_benefit = make(system, with_totals("mixed"))
    set_model_value(
        stored_housing_benefit,
        "housing_benefit_pre_benefit_cap",
        YEAR,
        np.array([0.0, 4_978.20, 0.0]),
    )
    with pytest.raises(ValueError, match="housing_benefit_pre_benefit_cap"):
        stored_housing_benefit.calculate("universal_credit", YEAR)


UC_HOUSEHOLD = st.fixed_dictionaries(
    dict(
        kind=st.just("uc"),
        universal_credit_pre_benefit_cap=st.floats(0, 40_000),
        uc_benefit_cap=st.sampled_from([14_753.0, 22_020.0]),
        child_benefit=st.sampled_from([0.0, 1_500.0]),
        employment_income=st.floats(0, 20_000),
    )
)
NON_DEPENDANT_HOUSEHOLD = st.fixed_dictionaries(
    dict(
        kind=st.just("nondep"),
        rent=st.sampled_from([3_000.0, 6_000.0]),
        employment_income=st.floats(0, 30_000),
        weekly_hours=st.sampled_from([0.0, 20.0, 35.0]),
        universal_credit_pre_benefit_cap=st.sampled_from([0.0, 5_000.0, 15_000.0]),
    )
)


def generated_population(households):
    """Each generated household, with its Universal Credit basket and the
    combined total it implies supplied for every benefit unit."""
    people, units, homes, basket = {}, {}, {}, {}
    for h, household in enumerate(households):
        if household["kind"] == "uc":
            claimant = f"uc_{h}"
            people[claimant] = dict(
                age=40,
                current_education="NOT_IN_EDUCATION",
                employment_income=household["employment_income"],
                weekly_hours=20.0,
            )
            units[claimant] = dict(
                members=[claimant],
                **{**NO_AWARDS, "child_benefit": household["child_benefit"]},
                would_claim_uc=True,
                uc_benefit_cap=household["uc_benefit_cap"],
                benunit_is_rent_liable=False,
                universal_credit_pre_benefit_cap=household[
                    "universal_credit_pre_benefit_cap"
                ],
            )
            basket[claimant] = (
                household["universal_credit_pre_benefit_cap"]
                + household["child_benefit"]
            )
            homes[f"home_{h}"] = dict(
                members=[claimant],
                country="ENGLAND",
                local_authority="MAIDSTONE",
                rent=0.0,
                tenure_type="RENT_PRIVATELY",
            )
        else:
            applicant, non_dependant = f"applicant_{h}", f"nondep_{h}"
            on_uc = household["universal_credit_pre_benefit_cap"] > 0
            people[applicant] = dict(age=70, current_education="NOT_IN_EDUCATION")
            people[non_dependant] = dict(
                age=40,
                current_education="NOT_IN_EDUCATION",
                employment_income=household["employment_income"],
                weekly_hours=household["weekly_hours"],
            )
            units[applicant] = dict(
                members=[applicant],
                **NO_AWARDS,
                would_claim_uc=False,
                uc_benefit_cap=14_753.0,
                benunit_is_rent_liable=True,
                universal_credit_pre_benefit_cap=0.0,
            )
            units[non_dependant] = dict(
                members=[non_dependant],
                **NO_AWARDS,
                would_claim_uc=on_uc,
                uc_benefit_cap=14_753.0,
                benunit_is_rent_liable=False,
                universal_credit_pre_benefit_cap=household[
                    "universal_credit_pre_benefit_cap"
                ],
            )
            basket[non_dependant] = household["universal_credit_pre_benefit_cap"]
            homes[f"home_{h}"] = dict(
                members=[applicant, non_dependant],
                country="ENGLAND",
                local_authority="MAIDSTONE",
                rent=household["rent"],
                tenure_type="RENT_PRIVATELY",
            )
    data = keyed(dict(people=people, benunits=units, households=homes), YEAR)
    # The supplied units hold no Housing Benefit in the cap: the claimants
    # pay no rent, and the applicants have reached pension age.
    supply(data, "uc_benefit_cap_welfare_benefits", basket)
    supply(data, "benefit_cap_welfare_benefits", basket)
    return data


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(
    households=st.lists(
        st.one_of(UC_HOUSEHOLD, NON_DEPENDANT_HOUSEHOLD), min_size=1, max_size=3
    )
)
def test_each_household_gets_its_results_alone(system, households):
    """For any mix of independent households, with Universal Credit's basket
    supplied, each household's Universal Credit, Housing Benefit and
    non-dependant deductions equal its results alone."""
    mixed = make(system, generated_population(households))
    alone = [
        make(system, generated_population([household])) for household in households
    ]
    for name in [
        "universal_credit",
        "housing_benefit",
        "housing_benefit_non_dep_deductions",
    ]:
        np.testing.assert_allclose(
            mixed.calculate(name, YEAR),
            np.concatenate([sim.calculate(name, YEAR) for sim in alone]),
            atol=0.01,
            err_msg=name,
        )


def test_computed_universal_credit_and_local_schemes(system):
    """With nothing supplied, Universal Credit's traced calculation reads no
    Housing Benefit variable but the reported award, and the national and
    local Council Tax Reduction schemes then read Universal Credit."""
    # Each local scheme's parameters start in 2026-27.
    year = 2026
    template = situation("mixed", year=year, full_uc=True)
    template["people"]["uc"]["housing_benefit_reported"] = {year: 6_000.0}
    data = {group: {} for group in template}
    for authority in [
        "MERTON",
        "KINGSTON_UPON_THAMES",
        "NEWHAM",
        "WESTMINSTER",
        "OXFORD",
    ]:
        prefix = authority.lower() + "_"
        for group, entities in template.items():
            for name, entity in entities.items():
                copied = copy.deepcopy(entity)
                if "members" in copied:
                    copied["members"] = [
                        prefix + member for member in copied["members"]
                    ]
                if group == "benunits":
                    # A reported Housing Benefit award otherwise makes
                    # claims_all_entitled_benefits false, so this family
                    # would not claim CTR by default.
                    copied["would_claim_council_tax_reduction"] = {year: True}
                if group == "households":
                    copied["local_authority"] = {year: authority}
                    copied["council_tax"] = {year: 2_000.0}
                data[group][prefix + name] = copied
    sim = make(system, data, year=year, trace=True)
    universal_credit = sim.calculate("universal_credit", year)
    names = traced_names(sim)
    assert universal_credit[0] > 0
    assert "uc_maximum_amount" in names
    assert "housing_benefit_reported" in names
    assert not {
        name
        for name in names
        if name.startswith("housing_benefit") and name != "housing_benefit_reported"
    }
    for name in [
        "housing_benefit",
        "council_tax_reduction",
        "merton_council_tax_reduction",
        "kingston_upon_thames_council_tax_reduction",
        "newham_council_tax_reduction",
        "westminster_council_tax_reduction",
        "oxford_council_tax_reduction",
    ]:
        values = sim.calculate(name, year)
        if name.endswith("_council_tax_reduction"):
            assert values.max() > 0, (name, values)


@pytest.mark.parametrize(
    "variable,parent",
    [
        ("uc_benefit_cap_welfare_benefits", Basket),
        ("universal_credit_pre_benefit_cap", PreCap),
    ],
)
def test_a_reform_reading_calculated_housing_benefit_raises_cycle_error(
    system, variable, parent
):
    """A reform that adds calculated Housing Benefit to Universal Credit's
    basket or award makes Universal Credit and the deductions depend on each
    other, and the engine raises CycleError."""

    def formula(benunit, period, parameters):
        return parent.formula(benunit, period, parameters) + benunit(
            "housing_benefit", period
        )

    replacement = type(variable, (parent,), dict(formula=formula))

    class CyclicReform(Reform):
        def apply(self):
            self.update_variable(replacement)

    data = situation("mixed")
    for unit in data["benunits"].values():
        unit.pop(variable, None)
    with pytest.raises(CycleError):
        make(CyclicReform(system), data).calculate("housing_benefit", YEAR)
