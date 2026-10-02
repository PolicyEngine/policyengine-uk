"""No Pension Credit child amount for a tax credit award.

SPC Regs 2002 reg 6(6)(d) adds the Schedule IIA amount for each child or
qualifying young person "except where paragraph (11) applies": where the
person "is awarded, or ... is treated as having an award of, a tax credit"
(reg 6(11)), child tax credit or working tax credit (reg 6(17)). Reg 6(6)(d)
and Schedule IIA apply from 1 February 2019 (SI 2018/676), so from 2019-20 in
the model. Tax credits ended on 5 April 2025. HMRC may award a tax credit at a
nil rate (TCA 2002 s.14(3)), so the award follows the claim and the
entitlement conditions other than the income test.

Properties, for any family:

1. The award is a claim plus the conditions of entitlement, recomputed
   independently, in every year with tax credits (2019-20 to 2024-25).
2. Differential: the child amount is nil where there is an award, and
   otherwise equals the amount in a simulation with the award entered as
   absent. That amount equals an independent Schedule IIA calculation from
   the parameters (para 9(1)(a) and para 10).
3. After tax credits ended (2025-26 on), no family has an award, and the
   child amount is the Schedule IIA amount.
4. Before 2019-20 the child amount is nil.
5. Removing the child amount never raises Pension Credit plus tax credits,
   and changes nothing for a family with no award.
6. The results do not depend on the order in which the child amount, the
   award, Pension Credit, the tax credit income test and household income
   are requested, and no request raises a dependency cycle.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

TAX_CREDIT_YEARS = [2019, 2021, 2024]
NO_AWARD_YEARS = [2025, 2026]
BEFORE_SCHEDULE_IIA_YEARS = [2015, 2018]
SUPPORT = ["pension_credit", "working_tax_credit", "child_tax_credit"]
OUTPUTS = [
    "child_minimum_guarantee_addition",
    "has_tax_credit_award",
    "tax_credits_applicable_income",
    "pension_credit",
    "working_tax_credit",
    "child_tax_credit",
]


@st.composite
def adults(draw, partner):
    age = draw(st.integers(40 if partner else 60, 90))
    earnings = draw(st.sampled_from([0, 0, 2_600, 6_000, 12_000]))
    return {
        "age": age,
        "employment_income": earnings,
        "weekly_hours": draw(st.sampled_from([16, 20, 30])) if earnings else 0,
        "state_pension": (
            draw(st.sampled_from([0, 4_000, 6_000, 9_000, 11_500])) if age >= 66 else 0
        ),
        "private_pension_income": draw(st.sampled_from([0, 0, 1_500, 5_000])),
        "savings_interest_income": draw(st.sampled_from([0, 0, 300, 500])),
        "working_tax_credit_reported": draw(st.sampled_from([0, 1])),
        "child_tax_credit_reported": draw(st.sampled_from([0, 1, 1])),
    }


@st.composite
def families(draw):
    members = [draw(adults(partner=False))]
    if draw(st.booleans()):
        members.append(draw(adults(partner=True)))
    children = [
        {"age": draw(st.integers(0, 15))} for _ in range(draw(st.integers(0, 3)))
    ]
    benunit = {
        "would_claim_pc": draw(st.sampled_from([True, True, True, False])),
        # A Universal Credit claim leaves a reported CTC award ineligible.
        "would_claim_uc": draw(st.sampled_from([False, False, False, True])),
    }
    household = {"savings": draw(st.sampled_from([0, 5_000, 12_000, 20_000]))}
    return members, children, benunit, household


def situation(families, year, benunit_inputs=None):
    people, benunits, households = {}, {}, {}
    for i, (members, children, benunit, household) in enumerate(families):
        names = []
        for j, inputs in enumerate(members):
            name = f"a{i}_{j}"
            people[name] = {k: {year: v} for k, v in inputs.items()}
            people[name]["is_claimant_or_partner"] = {year: True}
            names.append(name)
        for j, inputs in enumerate(children):
            name = f"c{i}_{j}"
            people[name] = {k: {year: v} for k, v in inputs.items()}
            people[name]["is_claimant_or_partner"] = {year: False}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            **{k: {year: v} for k, v in benunit.items()},
            **{k: {year: v} for k, v in (benunit_inputs or {}).items()},
        }
        households[f"h{i}"] = {
            "members": names,
            **{k: {year: v} for k, v in household.items()},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(drawn, year, order=OUTPUTS, benunit_inputs=None):
    sim = Simulation(situation=situation(drawn, year, benunit_inputs))
    return {variable: sim.calculate(variable, year) for variable in order}


def schedule_iia_amount(drawn, year):
    """Schedule IIA amounts from the parameters, for children who are not
    disabled: para 9(1)(a) for each child, and para 10's higher amount for
    the eldest if born before 6 April 2017 (by birth year, as the model)."""
    from policyengine_uk import CountryTaxBenefitSystem

    child = (
        CountryTaxBenefitSystem()
        .parameters(year)
        .gov.dwp.pension_credit.guarantee_credit.child
    )
    amounts = []
    for _, children, _, _ in drawn:
        ages = [c["age"] for c in children]
        if not ages:
            amounts.append(0)
            continue
        eldest_first = year - max(ages) < 2017
        weekly = len(ages) * child.addition
        if eldest_first:
            weekly += child.first.addition - child.addition
        amounts.append(weekly * 52)
    return np.array(amounts)


SETTINGS = settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
FAMILIES = st.lists(families(), min_size=1, max_size=6)

# The YAML households (child_amount_tax_credit_award.yaml), run on every
# invocation. Pension Credit earnings are net of SPC Regs Sch VI para 5, and
# the CTC family element is entered at its statutory £545.
_GRANDPARENT = {
    "age": 70,
    "employment_income": 2_600,
    "weekly_hours": 20,
    "state_pension": 4_000,
    "savings_interest_income": 300,
}
_INPUTS = {"would_claim_uc": False, "pension_credit_earnings": 2_080}
YAML_FAMILIES = [
    # CTC and WTC with Pension Credit: passported, no child amount.
    (
        [
            {
                **_GRANDPARENT,
                "child_tax_credit_reported": 1,
                "working_tax_credit_reported": 1,
            },
            {"age": 70, "state_pension": 4_000},
        ],
        [{"age": 10}],
        {**_INPUTS, "CTC_family_element": 545},
        {"savings": 10_000},
    ),
    # No tax credit claim: the child amount.
    (
        [_GRANDPARENT, {"age": 70, "state_pension": 4_000}],
        [{"age": 10}],
        _INPUTS,
        {"savings": 10_000},
    ),
    # WTC alone.
    (
        [
            {**_GRANDPARENT, "working_tax_credit_reported": 1},
            {"age": 70, "state_pension": 4_000},
        ],
        [{"age": 10}],
        _INPUTS,
        {"savings": 10_000},
    ),
    # A WTC award at a nil rate.
    (
        [
            {
                **_GRANDPARENT,
                "employment_income": 3_500,
                "state_pension": 9_000,
                "working_tax_credit_reported": 1,
            },
            {"age": 70, "state_pension": 8_000},
        ],
        [{"age": 10}],
        {**_INPUTS, "pension_credit_earnings": 2_980},
        {"savings": 10_000},
    ),
]


@SETTINGS
@given(FAMILIES, st.sampled_from(TAX_CREDIT_YEARS))
@example(YAML_FAMILIES, 2024)
def test_award_removes_the_child_amount_and_nothing_else(drawn, year):
    conditions = [
        "would_claim_CTC",
        "is_CTC_eligible",
        "would_claim_WTC",
        "is_WTC_eligible",
    ]
    on = calculate(drawn, year, order=OUTPUTS + conditions)
    # 1. The award is a claim plus the conditions of entitlement.
    expected_award = (on["would_claim_CTC"] & on["is_CTC_eligible"]) | (
        on["would_claim_WTC"] & on["is_WTC_eligible"]
    )
    assert (on["has_tax_credit_award"] == expected_award).all(), drawn
    # 2. Differential, and the Schedule IIA amount from the parameters.
    without = calculate(drawn, year, benunit_inputs={"has_tax_credit_award": False})
    expected = np.where(
        on["has_tax_credit_award"], 0, without["child_minimum_guarantee_addition"]
    )
    assert np.allclose(on["child_minimum_guarantee_addition"], expected), drawn
    assert np.allclose(
        without["child_minimum_guarantee_addition"],
        schedule_iia_amount(drawn, year),
        atol=0.01,
    ), drawn
    # 5. Removing the child amount never raises Pension Credit plus tax
    # credits, and changes nothing without an award.
    total_on = sum(on[v] for v in SUPPORT)
    total_without = sum(without[v] for v in SUPPORT)
    assert (total_on <= total_without + 0.01).all(), drawn
    no_award = ~on["has_tax_credit_award"]
    for variable in SUPPORT + ["tax_credits_applicable_income"]:
        assert np.allclose(on[variable][no_award], without[variable][no_award]), (
            variable,
            drawn,
        )


@SETTINGS
@given(FAMILIES, st.sampled_from(NO_AWARD_YEARS))
def test_no_award_after_tax_credits_ended(drawn, year):
    on = calculate(drawn, year)
    assert not on["has_tax_credit_award"].any()
    assert np.allclose(
        on["child_minimum_guarantee_addition"],
        schedule_iia_amount(drawn, year),
        atol=0.01,
    ), drawn


@SETTINGS
@given(FAMILIES, st.sampled_from(BEFORE_SCHEDULE_IIA_YEARS))
def test_no_child_amount_before_schedule_iia(drawn, year):
    on = calculate(drawn, year)
    assert (on["child_minimum_guarantee_addition"] == 0).all(), drawn


@SETTINGS
@given(FAMILIES, st.sampled_from(TAX_CREDIT_YEARS + NO_AWARD_YEARS))
@example(YAML_FAMILIES, 2024)
def test_results_do_not_depend_on_request_order(drawn, year):
    forward = calculate(drawn, year)
    backward = calculate(drawn, year, order=list(reversed(OUTPUTS)))
    household_first = calculate(drawn, year, order=["household_net_income"] + OUTPUTS)
    for variable in OUTPUTS:
        assert np.allclose(forward[variable], backward[variable]), (variable, drawn)
        assert np.allclose(forward[variable], household_first[variable]), (
            variable,
            drawn,
        )


def test_yaml_families_reach_every_case():
    """The pinned examples are not vacuous: they hit each case of the rule."""
    year = 2024
    on = calculate(YAML_FAMILIES, year)
    without = calculate(
        YAML_FAMILIES, year, benunit_inputs={"has_tax_credit_award": False}
    )
    assert on["has_tax_credit_award"].tolist() == [True, False, True, True]
    # The rule removes the child amount from each awarded family.
    assert (without["child_minimum_guarantee_addition"] > 0).all()
    assert np.allclose(on["child_minimum_guarantee_addition"], [0, 3_993.08, 0, 0])
    # Pension Credit, CTC and WTC are all paid to the first family.
    for variable in SUPPORT:
        assert on[variable][0] > 0, variable
    # The nil-rate award: no WTC, no Pension Credit, no child amount.
    assert on["working_tax_credit"][3] == 0
    assert on["pension_credit"][3] == 0
    assert without["pension_credit"][3] > 0
