"""Means tests count the claimant's and partner's income, nobody else's.

Invariant: for any benefit unit, giving income to a member who is neither the
claimant nor the partner (a child, a young person, or another adult in the
benefit unit) never changes a means test's income (UC Regs 2013 reg 22; HB
Regs 2006 reg 25; IS Regs 1987 reg 23; TCA 2002 s.7; CTR (Prescribed
Requirements) (England) Regs 2012 Sch 1 para 11; SPCA 2002 s.5).

Each example builds families twice in one simulation: once with the other
member's income and once without, in separate households and benefit units.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2024
INCOME_TESTS = [
    "uc_earned_income",
    "uc_unearned_income",
    "housing_benefit_applicable_income",
    "income_support_applicable_income",
    "tax_credits_applicable_income",
    "council_tax_reduction_applicable_income",
    "pension_credit_income",
]
EDUCATIONS = ["NOT_IN_EDUCATION", "UPPER_SECONDARY", "TERTIARY"]
money = st.floats(0, 50_000, allow_nan=False, allow_infinity=False)


@st.composite
def families(draw):
    # A head, an optional partner, and one member who by construction is
    # neither claimant nor partner: a child under 16, a 16-19-year-old at
    # least 16 years younger than the head (presumed the head's child), or a
    # third adult no older than the partner (the partner, earlier in member
    # order, wins any age tie).
    kind = draw(st.sampled_from(["child", "presumed_child", "third_adult"]))
    if kind == "child":
        other_age = draw(st.integers(0, 15))
        head_age = draw(st.integers(25, 85))
    elif kind == "presumed_child":
        other_age = draw(st.integers(16, 19))
        head_age = draw(st.integers(other_age + 16, 85))
    else:
        head_age = draw(st.integers(25, 85))
    family = [
        {
            "age": head_age,
            "employment_income": draw(money),
            "private_pension_income": draw(money),
        }
    ]
    if kind == "third_adult" or draw(st.booleans()):
        partner_age = draw(st.integers(20, head_age))
        family.append({"age": partner_age, "employment_income": draw(money)})
    if kind == "third_adult":
        other_age = draw(st.integers(20, partner_age))
    family.append(
        {
            "age": other_age,
            "current_education": draw(st.sampled_from(EDUCATIONS)),
            "employment_income": draw(st.floats(1, 50_000)),
            "private_pension_income": draw(money),
            "savings_interest_income": draw(money),
        }
    )
    return family


def situation(families_):
    people, benunits, households = {}, {}, {}
    for i, family in enumerate(families_):
        names = []
        for j, inputs in enumerate(family):
            name = f"p{i}_{j}"
            people[name] = {k: {YEAR: v} for k, v in inputs.items()}
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        households[f"h{i}"] = {"members": names}
    return {"people": people, "benunits": benunits, "households": households}


@settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(st.lists(families(), min_size=1, max_size=6))
def test_income_of_non_claimants_never_counts(units):
    without = [
        family[:-1]
        + [
            {
                **family[-1],
                "employment_income": 0,
                "private_pension_income": 0,
                "savings_interest_income": 0,
            }
        ]
        for family in units
    ]
    sim = Simulation(situation=situation(units + without))
    claimant = sim.calculate("is_claimant_or_partner", YEAR)
    offsets = np.cumsum([0] + [len(f) for f in units])
    n = len(units)
    for i in range(n):
        # The generator's construction, checked against the model.
        assert not claimant[offsets[i + 1] - 1], units[i]
    for variable in INCOME_TESTS:
        values = sim.calculate(variable, YEAR)
        for i in range(n):
            assert abs(values[i] - values[n + i]) < 0.01, (variable, units[i])
