"""Prescribed benefits in Pension Credit and Housing Benefit income.

The State Pension Credit Regulations 2002 reg 15(1) prescribe "all social
security benefits" as income except a closed list. The list does not name
industrial injuries disablement benefit (IIDB), severe disablement allowance
(SDA), incapacity benefit (IB) or maternity allowance (MA). For IIDB it
excepts the constant attendance and exceptionally severe disablement
increases (reg 15(1)(c)-(e)), which the reported IIDB amount cannot separate.
Pension-age Housing Benefit counts the same benefits under HB (SPC) Regs 2006
reg 29(1)(j), whose exceptions for these benefits match reg 15(1)'s. Reg 9
makes working tax credit, IB, SDA, MA, contribution-based JSA and contributory
ESA non-qualifying income for Savings Credit; IIDB stays qualifying income.

Draws: single people and couples over State Pension age in England, Wales or
Scotland, renting from the council in 2026, with State Pension, a private
pension and any of the four benefits (each on a drawn member, at a drawn
amount). Some families also have a carer receiving Carer's Allowance or, in
Scotland, Carer Support Payment, so the sources #1952 added are covered
together with these. There are no earnings, pension contributions or
children, and capital is at most £10,000, so neither Pension Credit deemed
income nor Housing Benefit tariff income arises. The benefit amounts are
inputs standing for actual awards, independent of the model's rate formulas.

Invariants:

1. Differential: Pension Credit and pension-age Housing Benefit assess the
   same income. Where Guarantee Credit is not paid and Housing Benefit income
   is above its zero floor, Housing Benefit applicable income plus its income
   disregard equals Pension Credit income. The disregard is added back because
   the model applies the HB earnings disregard (HB (SPC) Regs Sch 4) whether or
   not there are earnings; there are none here. There is no other intended
   difference on this domain: both measures deduct the claimant's and
   partner's income tax and National Insurance, and neither counts the
   Scottish Carer Supplement (SPC Regs reg 15(1)(ri); HB (SPC) Regs reg
   29(1)(j)(xviiha)).
2. Guarantee Credit is non-increasing in each of the four benefits, and while
   it is positive it falls pound for pound with the extra Pension Credit
   income, which is the extra benefit less the extra income tax and National
   Insurance (the model taxes IB).
3. Savings Credit income never exceeds Pension Credit income. Adding an amount
   of a reg 9 source (working tax credit, IB, SDA, MA, contribution-based JSA
   or contributory ESA) changes Savings Credit income only through income tax
   and National Insurance, and never raises Savings Credit. Draws for this
   invariant are aged 77 or over: the model dates State Pension age as birth
   year plus the current State Pension age (66 in 2026), so they meet its
   test of reaching it before the 2016 Savings Credit cutoff.
4. Boundary: on the private-pension step where Guarantee Credit ends,
   household net income, excluding the TV licence fee, does not fall. The free
   TV licence for over-75s on Pension Credit is a genuine statutory cliff, so
   it is excluded, as in test_pension_credit_carer_income_properties.py.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PENSIONS = np.arange(0, 25_001, 500)
AMOUNTS = np.arange(0, 15_001, 1_250)
PRESCRIBED_BENEFITS = ("iidb", "sda", "incapacity_benefit", "maternity_allowance")
# Reg 9 sources and the input each is set through: the tax base reads
# reported contribution-based JSA and contributory ESA.
REG_9_INPUTS = {
    "working_tax_credit": "working_tax_credit",
    "incapacity_benefit": "incapacity_benefit",
    "sda": "sda",
    "maternity_allowance": "maternity_allowance",
    "jsa_contrib": "jsa_contrib_reported",
    "esa_contrib": "esa_contrib_reported",
}
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
REGIONS = {
    "ENGLAND": "NORTH_WEST",
    "WALES": "WALES",
    "SCOTLAND": "SCOTLAND",
}


def money(high, low=0):
    return st.floats(low, high, allow_nan=False, allow_infinity=False)


@st.composite
def family(draw, min_age=67, high=12_000, state_pension=15_000):
    adults = [
        dict(
            age=draw(st.integers(min_age, 95)),
            state_pension=draw(money(state_pension)),
        )
        for _ in range(draw(st.integers(1, 2)))
    ]
    members = st.integers(0, len(adults) - 1)
    return dict(
        adults=adults,
        # Each benefit goes to one drawn member; an amount of zero is common.
        benefits={
            benefit: (draw(members), draw(st.one_of(st.just(0.0), money(high))))
            for benefit in PRESCRIBED_BENEFITS
        },
        # As in #1952, at most one carer, by caring hours or a reported award.
        carer=draw(st.one_of(st.none(), members)),
        by_hours=draw(st.booleans()),
        country=draw(st.sampled_from(tuple(REGIONS))),
        rent=draw(money(12_000)),
        council_tax=draw(money(3_000)),
        savings=draw(st.one_of(st.just(0.0), money(10_000))),
    )


def situation(rows):
    """One benefit unit and household per (family, private pension, inputs) row.

    The inputs map a variable to an amount added to the family's first adult,
    or set for the benefit unit when the variable is working tax credit.
    """
    people, benunits, households = {}, {}, {}
    for r, (fam, pension, inputs) in enumerate(rows):
        names = []
        for j, a in enumerate(fam["adults"]):
            name = f"p{r}_{j}"
            person = {
                "age": {YEAR: a["age"]},
                "state_pension": {YEAR: a["state_pension"]},
                # All private pension goes to the first adult.
                "private_pension_income": {YEAR: float(pension) * (j == 0)},
            }
            for benefit, (recipient, amount) in fam["benefits"].items():
                person[benefit] = {YEAR: amount * (j == recipient)}
            if j == fam["carer"]:
                if fam["by_hours"]:
                    person["care_hours"] = {YEAR: 35}
                else:
                    person["carers_allowance_reported"] = {YEAR: 1}
            if j == 0:
                for variable, amount in inputs.items():
                    if variable != "working_tax_credit":
                        drawn = person.get(variable, {YEAR: 0.0})[YEAR]
                        person[variable] = {YEAR: drawn + float(amount)}
            people[name] = person
            names.append(name)
        benunit = {"members": names}
        if "working_tax_credit" in inputs:
            benunit["working_tax_credit"] = {YEAR: float(inputs["working_tax_credit"])}
        benunits[f"b{r}"] = benunit
        households[f"h{r}"] = {
            "members": names,
            "country": {YEAR: fam["country"]},
            "region": {YEAR: REGIONS[fam["country"]]},
            "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
            "rent": {YEAR: fam["rent"]},
            "council_tax": {YEAR: fam["council_tax"]},
            "savings": {YEAR: fam["savings"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(rows, shape, variables):
    """Each variable per benefit unit (summed over members), reshaped."""
    simulation = Simulation(situation=situation(rows))
    return {
        variable: np.asarray(
            simulation.calculate(variable, YEAR, map_to="benunit")
        ).reshape(shape)
        for variable in variables
    }


def pension_grid(families, variables):
    rows = [(fam, pension, {}) for fam in families for pension in PENSIONS]
    return calculate(rows, (len(families), len(PENSIONS)), variables)


def with_amount(fam, benefit, amount):
    """The family with one benefit's award set to amount, on its recipient."""
    recipient, _ = fam["benefits"][benefit]
    return {**fam, "benefits": {**fam["benefits"], benefit: (recipient, amount)}}


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_pension_credit_and_housing_benefit_assess_the_same_prescribed_benefits(
    families,
):
    g = pension_grid(
        families,
        [
            "guarantee_credit",
            "pension_credit_income",
            "housing_benefit_eligible",
            "housing_benefit_applicable_income",
            "housing_benefit_applicable_income_disregard",
        ],
    )
    hb_income = g["housing_benefit_applicable_income"]
    # Where Guarantee Credit is not paid, and away from the zero floor on
    # Housing Benefit income.
    compared = (
        (g["guarantee_credit"] <= 0)
        & g["housing_benefit_eligible"].astype(bool)
        & (hb_income > 0)
    )
    before_disregard = hb_income + g["housing_benefit_applicable_income_disregard"]
    pc_income = g["pension_credit_income"]
    assert np.allclose(before_disregard[compared], pc_income[compared], atol=0.01), (
        families,
        before_disregard[compared],
        pc_income[compared],
    )


@PROPERTY_SETTINGS
@given(st.lists(family(state_pension=8_000), min_size=1, max_size=4))
def test_guarantee_credit_falls_pound_for_pound_with_each_prescribed_benefit(
    families,
):
    rows = [
        (with_amount(fam, benefit, amount), 0, {})
        for fam in families
        for benefit in PRESCRIBED_BENEFITS
        for amount in AMOUNTS
    ]
    shape = (len(families), len(PRESCRIBED_BENEFITS), len(AMOUNTS))
    g = calculate(
        rows,
        shape,
        [
            "guarantee_credit",
            "pension_credit_income",
            "income_tax",
            "national_insurance",
        ],
    )
    gc = g["guarantee_credit"]
    pc_income = g["pension_credit_income"]
    tax = g["income_tax"] + g["national_insurance"]
    assert np.all(np.diff(gc, axis=-1) <= 0.01), (families, gc)
    # The extra Pension Credit income is the extra benefit less the extra tax.
    extra_income = np.diff(pc_income, axis=-1)
    positive_income = (pc_income[..., :-1] > 0) & (pc_income[..., 1:] > 0)
    assert np.allclose(
        extra_income[positive_income],
        (np.diff(AMOUNTS) - np.diff(tax, axis=-1))[positive_income],
        atol=0.01,
    ), (families, pc_income, tax)
    # While Guarantee Credit is paid, it falls by exactly that much.
    paid = gc[..., 1:] > 0
    assert np.allclose(-np.diff(gc, axis=-1)[paid], extra_income[paid], atol=0.01), (
        families,
        gc,
        pc_income,
    )


@PROPERTY_SETTINGS
@given(
    st.lists(
        family(min_age=77, high=3_000, state_pension=4_000), min_size=2, max_size=4
    ),
    # Private pensions that put qualifying income near the Savings Credit
    # window, so that Savings Credit is often payable before the addition.
    st.lists(money(18_000, low=8_000), min_size=4, max_size=4),
    money(15_000),
)
def test_reg_9_sources_change_savings_credit_income_only_through_tax(
    families, pensions, amount
):
    rows = [
        (fam, pension, {REG_9_INPUTS[source]: added})
        for fam, pension in zip(families, pensions)
        for source in REG_9_INPUTS
        for added in (0, amount)
    ]
    shape = (len(families), len(REG_9_INPUTS), 2)
    g = calculate(
        rows,
        shape,
        [
            "pension_credit_income",
            "savings_credit_income",
            "savings_credit",
            "income_tax",
            "national_insurance",
        ],
    )
    sc_income = g["savings_credit_income"]
    assert np.all(sc_income <= g["pension_credit_income"] + 0.01), (families, g)
    savings_credit = g["savings_credit"]
    assert np.all(savings_credit[..., 1] <= savings_credit[..., 0] + 0.01), (
        families,
        amount,
        savings_credit,
    )
    tax = g["income_tax"] + g["national_insurance"]
    extra_tax = tax[..., 1] - tax[..., 0]
    assert np.allclose(
        sc_income[..., 1], np.maximum(sc_income[..., 0] - extra_tax, 0), atol=0.01
    ), (families, amount, sc_income, tax)


@PROPERTY_SETTINGS
@given(st.lists(family(high=4_000, state_pension=4_000), min_size=1, max_size=4))
def test_net_income_does_not_fall_where_guarantee_credit_ends(families):
    g = pension_grid(
        families,
        [
            "guarantee_credit",
            "household_net_income",
            "tv_licence",
            "housing_benefit",
            "council_tax_benefit",
        ],
    )
    step = np.diff(g["household_net_income"] + g["tv_licence"], axis=1)
    gc = g["guarantee_credit"]
    ends = (gc[:, :-1] > 0) & (gc[:, 1:] <= 0)
    for i, fam in enumerate(families):
        for k in np.flatnonzero(ends[i]):
            assert step[i, k] >= -0.01, (
                fam,
                f"private pension {PENSIONS[k]} -> {PENSIONS[k + 1]}",
                f"net income change {step[i, k]:.2f}",
                f"HB {g['housing_benefit'][i, k]:.2f} -> "
                f"{g['housing_benefit'][i, k + 1]:.2f}",
                f"CTR {g['council_tax_benefit'][i, k]:.2f} -> "
                f"{g['council_tax_benefit'][i, k + 1]:.2f}",
            )
