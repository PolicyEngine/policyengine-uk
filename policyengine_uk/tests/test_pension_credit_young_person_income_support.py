"""Pension Credit's young person and their Income Support (SPC reg. 4A(5)).

A 16-year-old outside education, in a 70-year-old's benefit unit, reports
their own Income Support in 2025, when it is in payment. They are not the
claimant's qualifying young person, so the claimant gets no child addition,
until a reform removes Income Support. UC reg. 5(5) does not list income
support, so they stay a UC qualifying young person throughout.

A young carer who claims Income Support in their own benefit unit follows
the calculated award. While they receive it they are no qualifying young
person, so they count as another resident and end the severe disability
addition of a pensioner they live with (Sch. I para. 2(2)(f)). A reform that
ends the award restores that addition however it ends it.
"""

from itertools import product

import numpy as np
import pytest
from policyengine_core.model_api import YEAR as YEAR_PERIOD
from policyengine_core.reforms import Reform
from policyengine_core.variables import Variable

from policyengine_uk import Simulation
from policyengine_uk.entities import BenUnit

YEAR = 2025


class abolish_income_support(Reform):
    def apply(self):
        self.neutralize_variable("income_support")


class income_support(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR_PERIOD

    def formula(benunit, period, parameters):
        return benunit.filled_array(0)


class zero_income_support(Reform):
    def apply(self):
        self.update_variable(income_support)


def simulation(reform=None):
    young_person = {
        "age": 16,
        "is_benunit_head": False,
        "current_education": "NOT_IN_EDUCATION",
        "income_support_reported": 3_000,
    }
    parent = {"age": 70, "is_parent": True, "is_benunit_head": True}
    return Simulation(
        situation={
            "people": {
                name: {key: {YEAR: value} for key, value in inputs.items()}
                for name, inputs in (
                    ("parent", parent),
                    ("young_person", young_person),
                )
            },
            "benunits": {"benunit": {"members": ["parent", "young_person"]}},
            "households": {
                "household": {
                    "members": ["parent", "young_person"],
                    "country": {YEAR: "ENGLAND"},
                    "rent": {YEAR: 0},
                    "savings": {YEAR: 0},
                }
            },
        },
        reform=reform,
    )


def inputs_for(year, values):
    return {key: {year: value} for key, value in values.items()}


def young_carer_and_pensioner(reform=None, year=2024):
    young = {
        "age": 19,
        "date_of_birth": 20051002,
        "is_benunit_head": True,
        "is_claimant_or_partner": True,
        "is_carer_for_benefits": True,
        "care_hours": 35,
        "would_claim_carers_allowance": False,
        "current_education": "UPPER_SECONDARY",
        "age_started_or_accepted_current_education_or_training": 17,
        "income_support_reported": 1,
    }
    pensioner = {
        "age": 70,
        "is_benunit_head": True,
        "is_claimant_or_partner": True,
        "would_claim_carers_allowance": False,
        "attendance_allowance": 1_000,
    }
    return Simulation(
        situation={
            "people": {
                "young": inputs_for(year, young),
                "pensioner": inputs_for(year, pensioner),
            },
            "benunits": {
                "young_unit": {
                    "members": ["young"],
                    **inputs_for(
                        year, {"would_claim_IS": True, "would_claim_uc": False}
                    ),
                },
                "pensioner_unit": {
                    "members": ["pensioner"],
                    **inputs_for(
                        year, {"would_claim_pc": True, "would_claim_uc": False}
                    ),
                },
            },
            "households": {
                "home": {
                    "members": ["young", "pensioner"],
                    **inputs_for(year, {"country": "ENGLAND", "rent": 0, "savings": 0}),
                }
            },
        },
        reform=reform,
    )


def grid(year, reform=None):
    """A young person of each kind, with a pensioner in the same household."""
    people, benunits, households = {}, {}, {}
    cases = product(
        (16, 17, 18, 19),
        ("NOT_IN_EDUCATION", "UPPER_SECONDARY"),
        (0, 0.01, 3_000),
        (False, True),
        (False, True),
    )
    for index, (age, education, report, carer, shares_a_unit) in enumerate(cases):
        young, elder = f"young_{index}", f"elder_{index}"
        people[young] = inputs_for(
            year,
            {
                "age": age,
                "current_education": education,
                "income_support_reported": report,
                "is_carer_for_benefits": carer,
                "is_benunit_head": not shares_a_unit,
            },
        )
        people[elder] = inputs_for(
            year, {"age": 70, "is_parent": True, "is_benunit_head": True}
        )
        units = [[elder, young]] if shares_a_unit else [[elder], [young]]
        for number, members in enumerate(units):
            benunits[f"unit_{index}_{number}"] = {"members": members}
        households[f"household_{index}"] = {
            "members": [elder, young],
            **inputs_for(year, {"country": "ENGLAND", "rent": 0, "savings": 0}),
        }
    return Simulation(
        situation={
            "people": people,
            "benunits": benunits,
            "households": households,
        },
        reform=reform,
    )


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_own_income_support_ends_the_young_person_until_a_reform_removes_it():
    kept = simulation()
    removed = simulation(abolish_income_support)
    assert kept.calculate("is_on_income_support", YEAR).tolist() == [False, True]
    assert not removed.calculate("is_on_income_support", YEAR).any()
    assert kept.calculate(
        "is_qualifying_young_person_for_pension_credit", YEAR
    ).tolist() == [False, False]
    assert removed.calculate(
        "is_qualifying_young_person_for_pension_credit", YEAR
    ).tolist() == [False, True]
    assert kept.calculate("child_minimum_guarantee_addition", YEAR).tolist() == [0]
    assert removed.calculate("child_minimum_guarantee_addition", YEAR)[0] > 0
    for sim in (kept, removed):
        assert sim.calculate(
            "is_qualifying_young_person_for_universal_credit", YEAR
        ).tolist() == [False, True]


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
@pytest.mark.parametrize("ending", [zero_income_support, abolish_income_support])
def test_a_reform_ending_a_young_carers_award_restores_a_pensioners_addition(ending):
    year = 2024
    kept = young_carer_and_pensioner()
    ended = young_carer_and_pensioner(ending)
    assert kept.calculate("income_support", year)[0] > 0
    assert ended.calculate("income_support", year)[0] == 0
    assert kept.calculate(
        "is_qualifying_young_person_for_pension_credit", year
    ).tolist() == [False, False]
    assert ended.calculate(
        "is_qualifying_young_person_for_pension_credit", year
    ).tolist() == [True, False]
    addition = ended.calculate("severe_disability_minimum_guarantee_addition", year)[1]
    assert kept.calculate("severe_disability_minimum_guarantee_addition", year)[1] == 0
    assert addition > 0
    assert ended.calculate("pension_credit", year)[1] == pytest.approx(
        kept.calculate("pension_credit", year)[1] + addition
    )


@pytest.mark.parametrize(
    "first, second",
    [
        ("is_qualifying_young_person_for_pension_credit", "income_support"),
        ("income_support", "is_qualifying_young_person_for_pension_credit"),
        ("pension_credit", "is_on_income_support"),
    ],
)
def test_pension_credit_status_and_income_support_calculate_in_either_order(
    first, second
):
    reference = young_carer_and_pensioner()
    sim = young_carer_and_pensioner()
    sim.calculate(first, 2024)
    for variable in (first, second):
        assert sim.calculate(variable, 2024).tolist() == (
            reference.calculate(variable, 2024).tolist()
        )


def test_labour_supply_responses_calculate_without_recursing_through_the_status():
    year = 2024
    sim = young_carer_and_pensioner(
        {
            "gov.simulation.labour_supply_responses.income_elasticity": {
                str(year): -0.05
            },
            "gov.simulation.labour_supply_responses.substitution_elasticity": {
                str(year): 0.15
            },
        }
    )
    assert sim.calculate(
        "is_qualifying_young_person_for_pension_credit", year
    ).tolist() == [False, False]
    assert sim.calculate("pension_credit", year)[1] > 0


@pytest.mark.parametrize("year", [2025, 2026])
def test_nobody_on_income_support_is_a_pension_credit_young_person(year):
    sim = grid(year)
    on_income_support = sim.calculate("is_on_income_support", year)
    young_person = sim.calculate("is_qualifying_young_person_for_pension_credit", year)
    assert not np.any(on_income_support & young_person)


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_zeroing_or_neutralizing_income_support_gives_claimants_the_same_status():
    year = 2025
    zeroed = grid(year, zero_income_support)
    neutralized = grid(year, abolish_income_support)
    claimant = zeroed.calculate("is_claimant_or_partner", year)
    for variable in (
        "is_on_income_support",
        "is_qualifying_young_person_for_pension_credit",
    ):
        assert (
            zeroed.calculate(variable, year)[claimant].tolist()
            == neutralized.calculate(variable, year)[claimant].tolist()
        )
