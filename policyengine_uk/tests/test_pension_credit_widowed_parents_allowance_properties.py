"""Widowed parent's allowance in Pension Credit and Housing Benefit income.

The State Pension Credit Regulations 2002 reg 15(1) prescribe "all social
security benefits" as income except a closed list. The list excepts
bereavement support payment (n) but not widowed parent's allowance (WPA).
Sch IV para 7 (applied by reg 17(7)) disregards £10 a week of each member's
WPA, and reg 9 does not make it non-qualifying income for Savings Credit.
Pension-age Housing Benefit counts it less £15 a week (HB (SPC) Regs 2006
Sch 5 para 7).

SSCBA 1992 s.39A(4) and (5) end the allowance at pensionable age and suspend
it while the recipient lives with a partner, so a lawful award should not meet
either assessment. The model takes a reported award as given, though, and WPA
overlaps with Carer's Allowance and Carer Support Payment. While Pension Credit
left WPA out, an award that displaced either carer's benefit raised Guarantee
Credit by the amount displaced; counted less £10 a week, it raises Guarantee
Credit by at most the disregard.

Draws: the families of test_pension_credit_prescribed_benefits_properties.py
(single people and couples over State Pension age, some with a carer), with a
WPA award added to the first adult.

Invariants:

1. Extra Pension Credit income is the extra WPA above £10 a week, less the
   extra income tax and National Insurance, less any Carer's Allowance or
   Carer Support Payment it displaces. While Guarantee Credit is positive it
   falls pound for pound with that income, and it never rises where no
   carer's benefit is displaced.
2. Differential: where neither Guarantee Credit nor Savings Credit is due and
   Housing Benefit income is above its zero floor, Housing Benefit applicable
   income equals Pension Credit income less the extra £5 a week Housing
   Benefit disregards: min(WPA, £15 x 52) - min(WPA, £10 x 52).
3. Savings Credit income moves with Pension Credit income: WPA is qualifying
   income, so adding it changes Savings Credit income by exactly the change in
   Pension Credit income wherever neither is at its zero floor.
"""

import numpy as np
from hypothesis import example, given
from hypothesis import strategies as st

from policyengine_uk.tests.test_pension_credit_prescribed_benefits_properties import (
    AMOUNTS,
    PENSIONS,
    PRESCRIBED_BENEFITS,
    INCOME_TAX,
    PROPERTY_SETTINGS,
    calculate,
    family,
    money,
)

WPA = "widowed_parents_allowance"
# Over the model's 52-week year: SPC Regs 2002 Sch IV para 7, £10 a week;
# HB (SPC) Regs 2006 Sch 5 para 7, £15 a week.
PC_DISREGARD = 10 * 52
HB_DISREGARD = 15 * 52


def carer(country):
    """A single pensioner with no State Pension who cares 35 hours a week."""
    return dict(
        adults=[dict(age=70, state_pension=0.0)],
        benefits={benefit: (0, 0.0) for benefit in PRESCRIBED_BENEFITS},
        carer=0,
        by_hours=True,
        country=country,
        rent=6_000.0,
        council_tax=1_500.0,
        savings=0.0,
    )


# Carer's Allowance in England and Carer Support Payment in Scotland, each
# paid in full until WPA displaces it.
CARERS = [carer("ENGLAND"), carer("SCOTLAND")]


def test_an_award_that_displaces_a_carer_benefit_raises_guarantee_credit_by_the_disregard():
    for fam in CARERS:
        g = calculate(
            [(fam, 0, {}), (fam, 0, {WPA: 1_000})],
            (2,),
            [
                "guarantee_credit",
                "pension_credit_income",
                "carers_allowance",
                "carer_support_payment",
                INCOME_TAX,
            ],
        )
        carer_benefit = g["carers_allowance"] + g["carer_support_payment"]
        assert np.allclose(np.diff(carer_benefit), -1_000, atol=0.01), (fam, g)
        assert np.allclose(g[INCOME_TAX], 0, atol=0.01), (fam, g)
        assert g["guarantee_credit"][0] > 1_000, (fam, g)
        # 1,000 of WPA counts as 480 and displaces 1,000 of the carer's
        # benefit, so Pension Credit income falls by the 520 disregarded.
        assert np.allclose(
            np.diff(g["pension_credit_income"]), -PC_DISREGARD, atol=0.01
        ), (fam, g)
        assert np.allclose(np.diff(g["guarantee_credit"]), PC_DISREGARD, atol=0.01), (
            fam,
            g,
        )


@PROPERTY_SETTINGS
@given(st.lists(family(state_pension=8_000), min_size=1, max_size=4))
@example(CARERS)
def test_guarantee_credit_falls_pound_for_pound_with_widowed_parents_allowance(
    families,
):
    rows = [(fam, 0, {WPA: amount}) for fam in families for amount in AMOUNTS]
    g = calculate(
        rows,
        (len(families), len(AMOUNTS)),
        [
            "guarantee_credit",
            "pension_credit_income",
            INCOME_TAX,
            "national_insurance",
            "carers_allowance",
            "carer_support_payment",
        ],
    )
    gc = g["guarantee_credit"]
    pc_income = g["pension_credit_income"]
    tax = g[INCOME_TAX] + g["national_insurance"]
    carer_benefit = g["carers_allowance"] + g["carer_support_payment"]
    displaced = np.diff(carer_benefit, axis=-1) < -0.01
    assert np.all(np.diff(gc, axis=-1)[~displaced] <= 0.01), (families, gc)
    extra_income = np.diff(pc_income, axis=-1)
    positive_income = (pc_income[..., :-1] > 0) & (pc_income[..., 1:] > 0)
    counted = np.maximum(AMOUNTS - PC_DISREGARD, 0)
    expected = (
        np.diff(counted) - np.diff(tax, axis=-1) + np.diff(carer_benefit, axis=-1)
    )
    assert np.allclose(
        extra_income[positive_income], expected[positive_income], atol=0.01
    ), (families, pc_income, tax, carer_benefit)
    paid = gc[..., 1:] > 0
    assert np.allclose(-np.diff(gc, axis=-1)[paid], extra_income[paid], atol=0.01), (
        families,
        gc,
        pc_income,
    )


@PROPERTY_SETTINGS
@given(
    st.lists(family(high=4_000, state_pension=4_000), min_size=1, max_size=4),
    money(15_000),
)
def test_housing_benefit_counts_widowed_parents_allowance_less_15_a_week(
    families, amount
):
    rows = [(fam, pension, {WPA: amount}) for fam in families for pension in PENSIONS]
    g = calculate(
        rows,
        (len(families), len(PENSIONS)),
        [
            "guarantee_credit",
            "savings_credit",
            "pension_credit_income",
            "housing_benefit_eligible",
            "housing_benefit_applicable_income",
        ],
    )
    hb_income = g["housing_benefit_applicable_income"]
    compared = (
        (g["guarantee_credit"] <= 0)
        & (g["savings_credit"] <= 0)
        & g["housing_benefit_eligible"].astype(bool)
        & (hb_income > 0)
    )
    expected = g["pension_credit_income"] - (
        min(amount, HB_DISREGARD) - min(amount, PC_DISREGARD)
    )
    assert np.allclose(hb_income[compared], expected[compared], atol=0.01), (
        families,
        amount,
        hb_income[compared],
        expected[compared],
    )


@PROPERTY_SETTINGS
@given(
    st.lists(
        family(min_age=77, high=3_000, state_pension=4_000), min_size=2, max_size=4
    ),
    # Private pensions that put qualifying income near the Savings Credit
    # window, as in the reg 9 property.
    st.lists(money(18_000, low=8_000), min_size=4, max_size=4),
    money(15_000),
)
def test_savings_credit_income_moves_with_pension_credit_income(
    families, pensions, amount
):
    rows = [
        (fam, pension, {WPA: added})
        for fam, pension in zip(families, pensions)
        for added in (0, amount)
    ]
    g = calculate(
        rows,
        (len(families), 2),
        ["pension_credit_income", "savings_credit_income"],
    )
    pc_income = g["pension_credit_income"]
    sc_income = g["savings_credit_income"]
    unfloored = np.all(sc_income > 0, axis=-1)
    assert np.allclose(
        np.diff(sc_income, axis=-1)[unfloored],
        np.diff(pc_income, axis=-1)[unfloored],
        atol=0.01,
    ), (families, amount, pc_income, sc_income)
