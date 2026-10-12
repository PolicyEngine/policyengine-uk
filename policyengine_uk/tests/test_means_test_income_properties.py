"""A means test never counts the income of someone outside its family.

Invariant: for any benefit unit, giving income to a member who is neither the
claimant, the partner, nor the programme's own child or young person (for
example an 18- or 19-year-old presumed the claimant's child but not in
education, or a third adult) never changes a means test's income. The UC, HB,
IS, tax credit, CTR and Pension Credit income totals are covered.

Each example builds families twice in one simulation: once with the other
member's income and once without, in separate households and benefit units.
It does so with every family claiming Universal Credit (the default) and with
none claiming it: a family on Universal Credit has its whole Housing Benefit
income disregarded (SI 2006/213 Sch 5 para 4), so the Housing Benefit means
test is only exercised off it.
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
FAMILY_FLAGS = [
    "is_claimant_or_partner",
    "is_child_or_qualifying_young_person_for_universal_credit",
    "is_child_or_young_person_for_legacy_benefits",
    "is_child_or_qualifying_young_person_for_child_tax_credit",
]
money = st.floats(0, 50_000, allow_nan=False, allow_infinity=False)


@st.composite
def families(draw):
    # A head, an optional partner, and one member who by construction is
    # outside every programme's family: a 16-19-year-old at least 16 years
    # younger than the head (presumed the head's child) who is not in
    # non-advanced education, so no programme's young person; or a third adult
    # no older than the partner (the partner, earlier in member order, wins any
    # age tie).
    kind = draw(st.sampled_from(["presumed_child", "third_adult"]))
    if kind == "presumed_child":
        other_age = draw(st.integers(16, 19))
        head_age = draw(st.integers(other_age + 16, 85))
        education = draw(st.sampled_from(["NOT_IN_EDUCATION", "TERTIARY"]))
    else:
        head_age = draw(st.integers(25, 85))
        education = draw(st.sampled_from(EDUCATIONS))
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
            "current_education": education,
            "employment_income": draw(st.floats(1, 50_000)),
            "private_pension_income": draw(money),
            "savings_interest_income": draw(money),
        }
    )
    return family


def situation(families_, would_claim_uc=None):
    people, benunits, households = {}, {}, {}
    for i, family in enumerate(families_):
        names = []
        for j, inputs in enumerate(family):
            name = f"p{i}_{j}"
            people[name] = {k: {YEAR: v} for k, v in inputs.items()}
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        if would_claim_uc is not None:
            benunits[f"b{i}"]["would_claim_uc"] = {YEAR: would_claim_uc}
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
    for would_claim_uc in (None, False):
        sim = Simulation(situation=situation(units + without, would_claim_uc))
        offsets = np.cumsum([0] + [len(f) for f in units])
        n = len(units)
        for variable in FAMILY_FLAGS:
            flags = sim.calculate(variable, YEAR)
            for i in range(n):
                # The generator's construction, checked against the model.
                assert not flags[offsets[i + 1] - 1], (variable, units[i])
        for variable in INCOME_TESTS:
            values = sim.calculate(variable, YEAR)
            for i in range(n):
                assert abs(values[i] - values[n + i]) < 0.01, (
                    variable,
                    would_claim_uc,
                    units[i],
                )
