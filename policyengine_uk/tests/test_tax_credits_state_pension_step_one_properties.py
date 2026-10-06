"""State Pension is step-one pension income for tax credits.

SI 2002/2006 reg 3(1): Step One adds "the pension income (as defined in
regulation 5(1)), the investment income ..., the property income ..."; "If the
result of this step is £300 or less, it is treated as nil. If the result of
this step is more than £300, only the excess is taken into account". Pension
income includes "any pension to which section 577 ... of ITEPA applies" (reg
5(1)(a)), which is the State Pension (ITEPA 2003 s.577(1)), and reg 7(2) takes
it out of social security income, which is step two.

Properties, for any family:

1. Law oracle: tax_credits_current_year_income is the claimants' step-one
   income (State Pension, private pension, savings interest, dividends and
   property income) less £300, floored at nil, plus their step-two income
   (earnings, trading income, Carer's Allowance, Carer Support Payment,
   contribution-based JSA and ESA, Incapacity Benefit and miscellaneous
   income), computed here directly from the inputs.
2. Against the previous formula, which put the State Pension in step two
   (applied below as a reform): income never rises, and falls by exactly
   min(State Pension, max(0, £300 - other step-one income)), so by at most
   £300. It is unchanged where other step-one income is £300 or more.
3. State Pension is treated exactly as private pension income: moving an
   amount from one to the other never changes the income.
4. Awards in 2024-25: WTC and CTC never fall, and together rise by at most
   41% of £300 plus the £26 minimum award. Guarantee Credit, which counts
   working tax credit as income, never rises, and falls by no more than the
   working tax credit gained.
5. In 2025-26, with no tax credit awards, every award and Pension Credit
   equal the previous formula's.
6. Every component of social_security_income is counted exactly once: the
   State Pension in step one, the rest in step two.
"""

import numpy as np
from hypothesis import HealthCheck, event, example, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp import tax_credits_current_year_income as tc
from policyengine_uk.variables.gov.hmrc.income_tax.social_security_income import (
    social_security_income,
)

ACTIVE_YEAR = 2024  # 2024-25, the last year of tax credit awards
INACTIVE_YEAR = 2025
DISREGARD = 300
TAPER = 0.41
MIN_AWARD = 26
TOL = 0.05  # float32 arithmetic on sums up to about £100,000
OTHER_STEP_ONE = [
    "private_pension_income",
    "savings_interest_income",
    "dividend_income",
    "property_income",
]
STEP_TWO = [
    "employment_income",
    "self_employment_income",
    "carers_allowance",
    "carer_support_payment",
    "jsa_contrib_reported",
    "esa_contrib_reported",
    "incapacity_benefit_reported",
    "miscellaneous_income",
]
AWARDS = ["working_tax_credit", "child_tax_credit", "tax_credits"]
PENSION_CREDIT = ["guarantee_credit", "savings_credit", "pension_credit"]


class previous_tax_credits_current_year_income(tc.tax_credits_current_year_income):
    # The formula before this change: the State Pension in step two, through
    # social_security_income.
    def formula(benunit, period, parameters):
        person = benunit.members
        members = person("is_claimant_or_partner", period) | person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        TC = parameters(period).gov.dwp.tax_credits
        income = add_for_members(benunit, period, OTHER_STEP_ONE, members)
        income = max_(income - TC.means_test.non_earned_disregard, 0)
        step_two = [
            "employment_income",
            "self_employment_income",
            "social_security_income",
            "miscellaneous_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            step_two.append("basic_income")
        return income + add_for_members(benunit, period, step_two, members)


previous_tax_credits_current_year_income.__name__ = "tax_credits_current_year_income"


class state_pension_in_step_two(Reform):
    def apply(self):
        self.update_variable(previous_tax_credits_current_year_income)


# Amounts around the £300 disregard, so other step-one income falls below, at
# and above it.
small = st.sampled_from([0, 0, 0, 50, 150, 299.99, 300, 300.01, 1_000, 5_000])


def sometimes(amount):
    return st.sampled_from([0, 0, 0, amount])


@st.composite
def adults(draw):
    earnings = draw(st.sampled_from([0, 0, 2_600, 6_000, 12_000, 25_000]))
    # Half the adults have no other step-one income, where the change bites.
    other_step_one = draw(st.booleans())
    return {
        "age": draw(st.integers(25, 90)),
        "state_pension": draw(
            st.one_of(
                st.sampled_from([0, 0, 200, 4_000, 6_600, 9_500, 11_500]),
                st.floats(0, 15_000, allow_nan=False, allow_infinity=False),
            )
        ),
        **{s: draw(small) if other_step_one else 0 for s in OTHER_STEP_ONE},
        "employment_income": earnings,
        "weekly_hours": draw(st.sampled_from([10, 16, 20, 30])) if earnings else 0,
        "self_employment_income": draw(sometimes(3_000)),
        "carers_allowance": draw(sometimes(4_258.80)),
        "carer_support_payment": draw(sometimes(4_258.80)),
        "jsa_contrib_reported": draw(sometimes(3_000)),
        "esa_contrib_reported": draw(sometimes(5_000)),
        "incapacity_benefit_reported": draw(sometimes(4_000)),
        "miscellaneous_income": draw(sometimes(500)),
        "working_tax_credit_reported": draw(st.sampled_from([0, 1])),
        "child_tax_credit_reported": draw(st.sampled_from([0, 1])),
    }


@st.composite
def families(draw):
    members = [draw(adults())]
    if draw(st.booleans()):
        members.append(draw(adults()))
    children = [
        {"age": draw(st.integers(0, 15))} for _ in range(draw(st.integers(0, 2)))
    ]
    benunit = {"would_claim_pc": draw(st.sampled_from([True, True, False]))}
    household = {"savings": draw(st.sampled_from([0, 5_000, 12_000]))}
    return members, children, benunit, household


def situation(units):
    def at(value):
        return {year: value for year in (ACTIVE_YEAR, INACTIVE_YEAR)}

    people, benunits, households = {}, {}, {}
    for i, (members, children, benunit, household) in enumerate(units):
        names = []
        for j, inputs in enumerate(members):
            name = f"a{i}_{j}"
            people[name] = {k: at(v) for k, v in inputs.items()}
            people[name]["is_claimant_or_partner"] = at(True)
            names.append(name)
        for j, inputs in enumerate(children):
            name = f"c{i}_{j}"
            people[name] = {k: at(v) for k, v in inputs.items()}
            people[name]["is_claimant_or_partner"] = at(False)
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": at(False),
            **{k: at(v) for k, v in benunit.items()},
        }
        households[f"h{i}"] = {
            "members": names,
            **{k: at(v) for k, v in household.items()},
        }
    return {"people": people, "benunits": benunits, "households": households}


def law(members):
    """Reg 3(1) steps one and two, from the claimants' inputs."""
    state_pension = sum(m["state_pension"] for m in members)
    other_step_one = sum(m[s] for m in members for s in OTHER_STEP_ONE)
    step_two = sum(m[s] for m in members for s in STEP_TWO)
    income = max(state_pension + other_step_one - DISREGARD, 0) + step_two
    # The previous formula's loss of the disregard on State Pension.
    change = min(state_pension, max(0, DISREGARD - other_step_one))
    return income, change


def moved_to_private_pension(unit):
    members, children, benunit, household = unit
    moved = [
        {
            **m,
            "state_pension": 0,
            "private_pension_income": m["private_pension_income"] + m["state_pension"],
        }
        for m in members
    ]
    return moved, children, benunit, household


def calculate(sim, variables, year):
    return {v: np.asarray(sim.calculate(v, year)) for v in variables}


SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

# The YAML households (tax_credits_state_pension_step_one.yaml), run as
# examples: State Pension wholly, partly and not at all within the £300, and
# the case where Pension Credit is paid without the passport.
PENSIONER = {
    **{k: 0 for k in ["state_pension", *OTHER_STEP_ONE, *STEP_TWO]},
    "age": 70,
    "employment_income": 2_600,
    "weekly_hours": 20,
    "working_tax_credit_reported": 1,
    "child_tax_credit_reported": 0,
}
YAML_FAMILIES = [
    [
        (
            [{**PENSIONER, "state_pension": 9_500}],
            [],
            {"would_claim_pc": True},
            {"savings": 0},
        )
    ],
    [
        (
            [{**PENSIONER, "state_pension": 9_500, "savings_interest_income": 100}],
            [],
            {"would_claim_pc": True},
            {"savings": 0},
        )
    ],
    [
        (
            [{**PENSIONER, "state_pension": 8_500, "private_pension_income": 1_000}],
            [],
            {"would_claim_pc": True},
            {"savings": 0},
        )
    ],
    [
        (
            [{**PENSIONER, "state_pension": 6_600}],
            [],
            {"would_claim_pc": True},
            {"savings": 0},
        )
    ],
    [
        (
            [{**PENSIONER, "state_pension": 200}],
            [],
            {"would_claim_pc": False},
            {"savings": 0},
        )
    ],
]


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=6))
@example(YAML_FAMILIES[0])
@example(YAML_FAMILIES[1])
@example(YAML_FAMILIES[2])
@example(YAML_FAMILIES[3])
@example(YAML_FAMILIES[4])
def test_state_pension_is_step_one_income(units):
    n = len(units)
    sit = situation(units + [moved_to_private_pension(u) for u in units])
    new = Simulation(situation=sit)
    old = Simulation(situation=sit)
    old.apply_reform(state_pension_in_step_two)

    income = "tax_credits_current_year_income"
    outputs = [income, *AWARDS, *PENSION_CREDIT]
    new_values = calculate(new, outputs, ACTIVE_YEAR)
    old_values = calculate(old, outputs, ACTIVE_YEAR)
    new_inactive = calculate(new, outputs, INACTIVE_YEAR)
    old_inactive = calculate(old, outputs, INACTIVE_YEAR)

    def gain(v):
        return new_values[v][:n] - old_values[v][:n]

    for i, (members, *_rest) in enumerate(units):
        expected, change = law(members)
        context = (units[i], {k: v[i] for k, v in new_values.items()})
        # 1. The law, computed from the inputs.
        assert abs(new_values[income][i] - expected) < TOL, context
        # 2. Against the previous formula.
        assert abs(old_values[income][i] - new_values[income][i] - change) < TOL, (
            context
        )
        assert 0 <= change <= DISREGARD
        # 3. State Pension is treated as private pension income.
        assert abs(new_values[income][n + i] - new_values[income][i]) < TOL, context
        # 5. No awards from 2025-26: only the income figure can differ.
        for v in [*AWARDS, *PENSION_CREDIT]:
            assert abs(new_inactive[v][i] - old_inactive[v][i]) < TOL, (v, context)
        assert new_inactive["tax_credits"][i] == 0
        assert abs(old_inactive[income][i] - new_inactive[income][i] - change) < TOL

    # 4. Awards in 2024-25.
    for v in ["working_tax_credit", "child_tax_credit", "tax_credits"]:
        assert (gain(v) > -TOL).all(), (v, units)
    assert (gain("tax_credits") <= TAPER * DISREGARD + MIN_AWARD + TOL).all(), units
    assert (gain("guarantee_credit") < TOL).all(), units
    assert (-gain("guarantee_credit") <= gain("working_tax_credit") + TOL).all(), units

    # Coverage (pytest --hypothesis-show-statistics).
    for i, (members, *_rest) in enumerate(units):
        change = law(members)[1]
        event(
            "income change: "
            + ("none" if change == 0 else "£300" if change == DISREGARD else "partial")
        )
        for v in ["working_tax_credit", "child_tax_credit"]:
            if gain(v)[i] > TOL:
                event(f"{v} raised")
        if gain("guarantee_credit")[i] < -TOL:
            event("guarantee_credit lowered")


def test_social_security_income_is_counted_once():
    # Reg 7(2): the State Pension is pension income, not social security
    # income. Every other component of the model's social_security_income is
    # reg 7 social security income. A new component must be classified here.
    components = set(social_security_income.adds)
    assert "state_pension" in tc.STEP_ONE_INCOME
    assert "state_pension" not in tc.SOCIAL_SECURITY_INCOME
    assert components == set(tc.SOCIAL_SECURITY_INCOME) | {"state_pension"}
    assert not set(tc.STEP_ONE_INCOME) & set(tc.SOCIAL_SECURITY_INCOME)
