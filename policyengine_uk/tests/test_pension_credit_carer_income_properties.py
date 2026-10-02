"""Carers' benefits in Pension Credit income and the Guarantee Credit boundary.

Pension Credit income left out Carer's Allowance and Carer Support Payment,
although the State Pension Credit Regulations 2002 reg 15(1) prescribe "all
social security benefits" as income except those they list, and neither is
listed. Pension-age Housing Benefit counted both, and Council Tax Reduction
counted Carer's Allowance (it does not yet count Carer Support Payment: #1955).
While Guarantee Credit was paid, both were passported to their maximum and hid
the difference; when Guarantee Credit ended, both were assessed on the
Carer's Allowance that Pension Credit had ignored, so a pensioner couple whose
partner received it lost well over the £100 rise in their private pension at
that step.

The Scottish Carer Supplement, paid with Carer Support Payment from 15 March
2026, is the opposite case: SPC Regs reg 15(1)(ri) excepts it from Pension
Credit income, and HB (SPC) Regs 2006 reg 29(1)(j)(xviiha) excepts it from
Housing Benefit income. SI 2026/246 arts 17(3) and 21(3) inserted both. It is
taxable (SI 2026/93).

Invariants, for single people and couples over State Pension age in which one
member is a carer receiving Carer's Allowance (England and Wales) or Carer
Support Payment (Scotland), renting from the council in 2026:

1. Differential: Pension Credit and pension-age Housing Benefit assess the
   same income. Where Guarantee Credit is not paid, Housing Benefit
   applicable income plus its income disregard equals Pension Credit income.
   The draws have no earnings, no pension contributions and capital of at
   most £10,000, so neither tariff income nor the earnings rules apply.
2. Boundary: on the private-pension step where Guarantee Credit ends,
   household net income, excluding the TV licence fee, does not fall. The
   free TV licence for over-75s on Pension Credit is a genuine statutory
   cliff, so it is excluded.
3. Metamorphic: setting the Scottish Carer Supplement to zero changes
   Pension Credit income and Housing Benefit applicable income only through
   income tax: each plus income tax is unchanged. This encodes the model's
   current behaviour, not the law's. The law disregards tax only on income
   taken into account (SPC Regs reg 17(10); HB (SPC) Regs 2006 reg 33(12)),
   so the supplement should leave both measures unchanged outright, while
   the model deducts all income tax, including the tax on the supplement
   (#1954). When that is fixed, assert the measures themselves are unchanged.

These compare PolicyEngine's own income measures, so they hold whatever
carer's benefit the model pays. The model does not yet apply the
overlapping-benefit reduction of Carer's Allowance and Carer Support Payment
by State Pension (SPC Regs reg 15(4)(a) and (g)).

Only one member of a couple is drawn as a carer. Two carers in a couple get
two Pension Credit carer additions (SPC Regs reg 6(8)) but, until the couple
carer premium is set to twice the single rate, one Housing Benefit carer
premium, so invariant 2 does not yet hold for them. Disability benefits are
not drawn: with a carer benefit in payment in the benefit unit, Pension Credit
withholds its severe disability addition, but the Housing Benefit severe
disability premium keys on a different disability test.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PENSIONS = np.arange(0, 20_001, 500)
PROPERTY_SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
REGIONS = {
    "ENGLAND": "NORTH_WEST",
    "WALES": "WALES",
    "SCOTLAND": "SCOTLAND",
}
NO_SCOTTISH_CARER_SUPPLEMENT = {
    "gov.social_security_scotland.carer_support_payment.supplement": {
        "2026-01-01.2100-12-31": 0
    }
}


def money(high):
    return st.floats(0, high, allow_nan=False, allow_infinity=False)


@st.composite
def adult(draw):
    return dict(
        age=draw(st.integers(67, 95)),
        state_pension=draw(money(15_000)),
    )


@st.composite
def family(draw, countries=tuple(REGIONS)):
    adults = [draw(adult()) for _ in range(draw(st.integers(1, 2)))]
    return dict(
        adults=adults,
        carer=draw(st.integers(0, len(adults) - 1)),
        # The carer qualifies either by caring hours or by a reported award.
        by_hours=draw(st.booleans()),
        country=draw(st.sampled_from(countries)),
        rent=draw(money(12_000)),
        council_tax=draw(money(3_000)),
        savings=draw(st.one_of(st.just(0.0), money(10_000))),
    )


def situation(families):
    """Each family once per private pension on the PENSIONS grid."""
    people, benunits, households = {}, {}, {}
    for i, fam in enumerate(families):
        for k, pension in enumerate(PENSIONS):
            names = []
            for j, a in enumerate(fam["adults"]):
                name = f"p{i}_{k}_{j}"
                person = {
                    "age": {YEAR: a["age"]},
                    "state_pension": {YEAR: a["state_pension"]},
                    # All private pension goes to the first adult.
                    "private_pension_income": {YEAR: float(pension) * (j == 0)},
                }
                if j == fam["carer"]:
                    if fam["by_hours"]:
                        person["care_hours"] = {YEAR: 35}
                    else:
                        person["carers_allowance_reported"] = {YEAR: 1}
                people[name] = person
                names.append(name)
            benunits[f"b{i}_{k}"] = {"members": names}
            households[f"h{i}_{k}"] = {
                "members": names,
                "country": {YEAR: fam["country"]},
                "region": {YEAR: REGIONS[fam["country"]]},
                "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
                "rent": {YEAR: fam["rent"]},
                "council_tax": {YEAR: fam["council_tax"]},
                "savings": {YEAR: fam["savings"]},
            }
    return {"people": people, "benunits": benunits, "households": households}


def grid(families, reform=None):
    simulation = Simulation(situation=situation(families), reform=reform)
    shape = (len(families), len(PENSIONS))

    def get(variable):
        return np.asarray(simulation.calculate(variable, YEAR)).reshape(shape)

    def by_benunit(variable):
        values = simulation.calculate(variable, YEAR, map_to="benunit")
        return np.asarray(values).reshape(shape)

    g = {
        variable: get(variable)
        for variable in [
            "household_net_income",
            "tv_licence",
            "guarantee_credit",
            "pension_credit_income",
            "housing_benefit_eligible",
            "housing_benefit_applicable_income",
            "housing_benefit_applicable_income_disregard",
            "housing_benefit",
            "council_tax_benefit",
        ]
    }
    for variable in [
        "carers_allowance",
        "carer_support_payment",
        "scottish_carer_supplement",
        "income_tax",
    ]:
        g[variable] = by_benunit(variable)
    return g


def assert_carer_benefit_paid(g, i, fam):
    carer_benefit = g["carers_allowance"][i] + g["carer_support_payment"][i]
    assert np.all(carer_benefit > 0), fam


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_pension_credit_and_housing_benefit_assess_the_same_carer_income(families):
    g = grid(families)
    for i, fam in enumerate(families):
        assert_carer_benefit_paid(g, i, fam)
        hb_income = g["housing_benefit_applicable_income"][i]
        # Where Guarantee Credit is not paid, and away from the zero floor on
        # Housing Benefit income.
        compared = (
            (g["guarantee_credit"][i] <= 0)
            & g["housing_benefit_eligible"][i].astype(bool)
            & (hb_income > 0)
        )
        before_disregard = (
            hb_income + g["housing_benefit_applicable_income_disregard"][i]
        )
        pc_income = g["pension_credit_income"][i]
        assert np.allclose(
            before_disregard[compared], pc_income[compared], atol=0.01
        ), (fam, before_disregard[compared], pc_income[compared])


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_net_income_does_not_fall_where_guarantee_credit_ends_for_carers(families):
    g = grid(families)
    net = g["household_net_income"] + g["tv_licence"]
    step = np.diff(net, axis=1)
    gc = g["guarantee_credit"]
    ends = (gc[:, :-1] > 0) & (gc[:, 1:] <= 0)
    for i, fam in enumerate(families):
        assert_carer_benefit_paid(g, i, fam)
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


@PROPERTY_SETTINGS
@given(st.lists(family(countries=("SCOTLAND",)), min_size=1, max_size=4))
def test_scottish_carer_supplement_is_not_means_tested_income(families):
    g = grid(families)
    without = grid(families, reform=NO_SCOTTISH_CARER_SUPPLEMENT)
    for i, fam in enumerate(families):
        assert np.all(g["scottish_carer_supplement"][i] > 0), fam
        assert np.all(without["scottish_carer_supplement"][i] == 0), fam
        assert np.allclose(
            g["carer_support_payment"][i],
            without["carer_support_payment"][i],
        ), fam
        for variable in ["pension_credit_income", "housing_benefit_applicable_income"]:
            with_supplement = g[variable][i] + g["income_tax"][i]
            without_supplement = without[variable][i] + without["income_tax"][i]
            # Only where the zero floor does not bind in either run.
            compared = (g[variable][i] > 0) & (without[variable][i] > 0)
            assert np.allclose(
                with_supplement[compared],
                without_supplement[compared],
                atol=0.01,
            ), (fam, variable)
