"""Pension Credit's young person and their own Income Support (SPC reg. 4A(5)).

A 16-year-old outside education, in a 70-year-old's benefit unit, reports
their own Income Support in 2025, when it is in payment. They are not the
claimant's qualifying young person, so the claimant gets no child addition,
until a reform removes Income Support. UC reg. 5(5) does not list income
support, so they stay a UC qualifying young person throughout.
"""

import pytest
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation

YEAR = 2025


class abolish_income_support(Reform):
    def apply(self):
        self.neutralize_variable("income_support")


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


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_own_income_support_ends_the_young_person_until_a_reform_removes_it():
    kept = simulation()
    removed = simulation(abolish_income_support)
    assert kept.calculate("receives_income_support_in_own_right", YEAR).tolist() == [
        False,
        True,
    ]
    assert not removed.calculate("receives_income_support_in_own_right", YEAR).any()
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
