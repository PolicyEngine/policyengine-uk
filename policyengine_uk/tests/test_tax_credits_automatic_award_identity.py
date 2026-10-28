"""Automatic tax credits equal the automatic CTC and WTC awards.

HMRC's finalised-award definitions describe tax credits as Child Tax Credit
and Working Tax Credit. Generated public situations vary family composition,
earnings, hours and reported continuing claims. No tax-credit component,
eligibility, award, rate or aggregate is supplied directly.
"""

import numpy as np
from hypothesis import Phase, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation


YEAR = 2024
FAMILIES = st.lists(
    st.tuples(
        st.integers(min_value=1, max_value=2),
        st.integers(min_value=0, max_value=3),
        st.sampled_from([0, 4_000, 8_000, 25_000]),
        st.sampled_from([0, 10, 16, 24, 30]),
        st.sampled_from([0, 1_000]),
        st.sampled_from([0, 1_000]),
        st.booleans(),
    ),
    min_size=1,
    max_size=3,
)


@settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    database=None,
    phases=[Phase.generate],
)
@given(FAMILIES)
def test_tax_credits_equal_automatic_child_and_working_tax_credit(families):
    # A non-reporting family keeps the original eligibility defect represented
    # in every population, alongside the generated continuing-claim controls.
    families = [(1, 1, 4_000, 10, 0, 0, False), *families]
    people = {}
    benunits = {}
    households = {}
    for index, (adults, children, earnings, hours, ctc, wtc, reverse) in enumerate(
        families
    ):
        members = []
        for adult in range(adults):
            name = f"adult_{index}_{adult}"
            members.append(name)
            people[name] = {
                "age": {YEAR: 35 + adult},
                "is_parent": {YEAR: children > 0},
                "is_benunit_head": {YEAR: adult == 0},
                "is_claimant_or_partner": {YEAR: True},
                "employment_income": {YEAR: earnings if adult == 0 else 0},
                "weekly_hours": {YEAR: hours if adult == 0 else 0},
                "child_tax_credit_reported": {YEAR: ctc if adult == 0 else 0},
                "working_tax_credit_reported": {YEAR: wtc if adult == 0 else 0},
            }
        for child in range(children):
            name = f"child_{index}_{child}"
            members.append(name)
            age = [2, 4, 10][child]
            people[name] = {
                "age": {YEAR: age},
                "date_of_birth": {YEAR: (YEAR - age) * 10_000 + 101},
                "is_claimant_or_partner": {YEAR: False},
            }
        if reverse:
            members.reverse()
        benunits[f"benunit_{index}"] = {
            "members": members,
            "would_claim_uc": {YEAR: False},
        }
        households[f"household_{index}"] = {
            "members": members,
            "region": {YEAR: "WALES"},
        }
    simulation = Simulation(
        situation={
            "people": people,
            "benunits": benunits,
            "households": households,
        }
    )
    np.testing.assert_allclose(
        simulation.calculate("tax_credits", YEAR),
        simulation.calculate("child_tax_credit", YEAR)
        + simulation.calculate("working_tax_credit", YEAR),
        rtol=0,
        atol=0.01,
    )
