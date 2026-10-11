"""A benefit unit's claimant or partner is never its own child or qualifying
young person.

Child Benefit goes to a person responsible for a child or qualifying young
person, who has them living with them (SSCBA 1992 ss.141 and 143(1)); no one
gets it for their spouse, civil partner or partner (Child Benefit (General)
Regulations 2006 regs 12-13). A tax credit claimant is responsible for a child
or qualifying young person who normally lives with them, never for their own
partner (Child Tax Credit Regulations 2002 reg. 3(1) Rule 1, Cases G-H). A
Pension Credit claimant is responsible for one who normally lives with them,
not for one they live with as a couple (SPC Regs 2002 Sch. IIA para. 3).

Invariants, for Child Benefit, Child Tax Credit and Pension Credit:

1. No claimant or partner is the benefit unit's child or qualifying young
   person, for any benefit unit, ages and inputs.
2. A claimant's or partner's own age, education, training, benefit receipt
   and disability never change the benefit unit's Child Benefit entitlement,
   CTC child and disabled child elements, or Pension Credit child addition.
3. Every other member keeps the programme's status test: they are the
   unit's child or qualifying young person exactly when they are a child or
   qualifying young person for the programme (and, for CTC and Pension
   Credit, not looked after by a local authority). This restates the
   formula from the status variables, to hold the composition in place;
   invariants 2 and 4 and the oracle in
   test_child_and_adult_definitions_properties.py are the independent
   checks.
4. Child Benefit entitlement equals an independent count: the eldest such
   member at the eldest-child rate, each other at the additional rate, for
   52 weeks.

The household structure is supplied (is_claimant_or_partner), so the tests
exercise the programme rules and not the structural presumption, which
test_child_and_adult_definitions_properties.py covers.
"""

from unittest.mock import patch

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.tax_benefit_system import system
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)

YEARS = (2024, 2026)
_PROPERTY_SYSTEM = system.clone()
EDUCATIONS = tuple(item.name for item in EducationType)
PROGRAMMES = ("child_benefit", "child_tax_credit", "pension_credit")
CHILD_AMOUNTS = (
    "child_benefit_entitlement",
    "CTC_child_element",
    "CTC_disabled_child_element",
    "CTC_severely_disabled_child_element",
    "child_minimum_guarantee_addition",
)
SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

member = st.fixed_dictionaries(
    {
        "age": st.integers(0, 25),
        "current_education": st.sampled_from(EDUCATIONS),
        "is_in_approved_training": st.booleans(),
        "receives_benefits_in_own_right": st.booleans(),
        "is_looked_after_by_local_authority": st.booleans(),
        "is_disabled_for_benefits": st.booleans(),
        "is_severely_disabled_for_benefits": st.booleans(),
        "age_started_or_accepted_current_education_or_training": st.sampled_from(
            [17, 1000]
        ),
    }
)


@st.composite
def benefit_units(draw):
    """A claimant, an optional partner and up to four other members, all with
    arbitrary ages and inputs."""
    claimants = draw(st.lists(member, min_size=1, max_size=2))
    others = draw(st.lists(member, max_size=4))
    return [dict(p, is_claimant_or_partner=True) for p in claimants] + [
        dict(p, is_claimant_or_partner=False) for p in others
    ]


def simulate(units, year):
    situation = {"people": {}, "benunits": {}, "households": {}}
    people = []
    for i, unit in enumerate(units):
        names = []
        for j, inputs in enumerate(unit):
            name = f"p{i}_{j}"
            situation["people"][name] = {}
            people.append(inputs)
            names.append(name)
        situation["benunits"][f"b{i}"] = {"members": names}
        situation["households"][f"h{i}"] = {"members": names}
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=_PROPERTY_SYSTEM.clone,
    ):
        sim = Simulation(situation=situation)
    for variable in people[0]:
        sim.set_input(variable, year, [p[variable] for p in people])
    sim.input_variables = list(people[0])
    sim.reset_calculations()
    return sim


def split(values, units):
    out, offset = [], 0
    for unit in units:
        out.append(values[offset : offset + len(unit)])
        offset += len(unit)
    return out


@SETTINGS
@given(st.lists(benefit_units(), min_size=1, max_size=6), st.sampled_from(YEARS))
def test_claimants_are_never_their_units_children_and_others_keep_status(units, year):
    sim = simulate(units, year)
    claimant = np.array([p["is_claimant_or_partner"] for u in units for p in u])
    looked_after = np.array(
        [p["is_looked_after_by_local_authority"] for u in units for p in u]
    )
    for programme in PROGRAMMES:
        family = sim.calculate(
            f"is_child_or_qualifying_young_person_for_{programme}", year
        )
        status = sim.calculate(f"is_child_for_{programme}", year) | sim.calculate(
            f"is_qualifying_young_person_for_{programme}", year
        )
        # Invariant 1.
        assert not (family & claimant).any(), programme
        # Invariant 3.
        expected = status & ~claimant
        if programme != "child_benefit":
            expected &= ~looked_after
        np.testing.assert_array_equal(family, expected, err_msg=programme)


@SETTINGS
@given(
    st.lists(
        st.tuples(benefit_units(), st.lists(member, min_size=2, max_size=2)),
        min_size=1,
        max_size=5,
    ),
    st.sampled_from(YEARS),
)
def test_claimants_own_circumstances_never_change_child_amounts(pairs, year):
    # Invariant 2: each unit appears twice, the second time with its claimant
    # and any partner redrawn and every other member unchanged.
    original = [unit for unit, _ in pairs]
    redrawn = []
    for unit, replacements in pairs:
        copy, k = [], 0
        for p in unit:
            if p["is_claimant_or_partner"]:
                copy.append(dict(replacements[k], is_claimant_or_partner=True))
                k += 1
            else:
                copy.append(p)
        redrawn.append(copy)
    sim = simulate(original + redrawn, year)
    n = len(original)
    for variable in CHILD_AMOUNTS:
        values = sim.calculate(variable, year)
        np.testing.assert_allclose(values[:n], values[n:], err_msg=variable)


@SETTINGS
@given(st.lists(benefit_units(), min_size=1, max_size=6), st.sampled_from(YEARS))
def test_child_benefit_entitlement_counts_only_other_members(units, year):
    # Invariant 4, from status inputs and the weekly rates alone.
    sim = simulate(units, year)
    rates = sim.tax_benefit_system.parameters(f"{year}-06-01").gov.hmrc.child_benefit
    status = sim.calculate("is_child_for_child_benefit", year) | sim.calculate(
        "is_qualifying_young_person_for_child_benefit", year
    )
    entitlement = sim.calculate("child_benefit_entitlement", year)
    for unit, eligible, actual in zip(units, split(status, units), entitlement):
        counted = [
            e and not p["is_claimant_or_partner"] for p, e in zip(unit, eligible)
        ]
        number = sum(counted)
        weekly = (
            0
            if number == 0
            else rates.amount.eldest + (number - 1) * rates.amount.additional
        )
        np.testing.assert_allclose(actual, weekly * 52, rtol=1e-6)


def test_lone_qualifying_young_person_gets_no_child_amount_for_themselves():
    # Exhaustive over ages 15-20, every education value and training flag:
    # a lone claimant gets nothing for themselves, whatever their status.
    units = [
        [
            {
                "age": age,
                "current_education": education,
                "is_in_approved_training": training,
                "receives_benefits_in_own_right": False,
                "is_looked_after_by_local_authority": False,
                "is_disabled_for_benefits": False,
                "is_severely_disabled_for_benefits": False,
                "age_started_or_accepted_current_education_or_training": 17,
                "is_claimant_or_partner": True,
            }
        ]
        for age in range(15, 21)
        for education in EDUCATIONS
        for training in (False, True)
    ]
    for year in YEARS:
        sim = simulate(units, year)
        status = sim.calculate("is_qualifying_young_person_for_child_benefit", year)
        # Not vacuous: some of these claimants are qualifying young persons.
        assert status.any()
        for variable in CHILD_AMOUNTS:
            np.testing.assert_array_equal(
                sim.calculate(variable, year), 0, err_msg=variable
            )
