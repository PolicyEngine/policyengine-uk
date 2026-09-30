"""Pension-age severe disability premium and the Guarantee Credit boundary.

Pension Credit's minimum guarantee included the severe disability addition
for an Attendance Allowance recipient, but the Housing Benefit and Council
Tax Reduction applicable amounts did not include the severe disability
premium, because the legacy premium tested a narrower, tax-credit style
disability flag. While Guarantee Credit was paid, Housing Benefit was
passported to its maximum and hid the gap; when Guarantee Credit ended,
Housing Benefit fell by 65% of it. A single pensioner on Attendance
Allowance lost £2,040.52 of net income when private pension rose from
£11,900 to £12,000 in 2026.

Invariants, for single people and couples over State Pension age without
children or carers, who rent from the council in England in 2026:

1. Structural: where Housing Benefit is available, its applicable amount is
   at least the Pension Credit minimum guarantee, and so is the Council Tax
   Reduction applicable amount. In law the pension-age personal allowances
   (HB(SPC) Regs 2006 Sch 3 para 1; CTR (Prescribed Requirements) (England)
   Regs 2012 Sch 2 para 1) are at least the standard minimum guarantee (SPC
   Regs 2002 reg 6(1)), and the severe disability premium (Sch 3 paras 6 and
   12(1)) has the same conditions and amounts as the severe disability
   addition (SPC Regs Sch I para 1 and reg 6(5)).
2. Boundary: on the private-pension step where Guarantee Credit ends,
   household net income, excluding the TV licence fee, does not fall. The
   free TV licence for over-75s on Pension Credit is a genuine statutory
   cliff, so it is excluded.
3. Schedule: over State Pension age the premium is a whole number (0, 1 or
   2) of weekly severe disability rates, equals the Pension Credit severe
   disability addition, and is the only premium besides the carer premium;
   below State Pension age it is zero and benefits_premiums is the sum of the
   four legacy premiums, so working-age applicable amounts are unchanged.

Carers are not drawn: the invariants for carers also depend on Pension
Credit income counting Carer's Allowance and on the carer premium per carer,
which are separate changes. Full monotonicity in income is not asserted: it
also depends on the savings-credit-only income rules for Housing Benefit and
Council Tax Reduction (HB(SPC) Regs 2006 reg 27 and the CTR equivalents),
which are likewise separate.
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
DISABILITY = st.sampled_from(
    [
        {},
        {"aa_category": "LOWER"},
        {"aa_category": "HIGHER"},
        {"dla_sc_category": "LOWER"},
        {"dla_sc_category": "MIDDLE"},
        {"dla_sc_category": "HIGHER"},
        {"pip_dl_category": "STANDARD"},
        {"pip_dl_category": "ENHANCED"},
    ]
)


def money(high):
    return st.floats(0, high, allow_nan=False, allow_infinity=False)


@st.composite
def adult(draw):
    return dict(
        age=draw(st.integers(67, 95)),
        disability=draw(DISABILITY),
        blind=draw(st.booleans()),
        state_pension=draw(money(15_000)),
    )


@st.composite
def family(draw):
    return dict(
        adults=[draw(adult()) for _ in range(draw(st.integers(1, 2)))],
        rent=draw(money(12_000)),
        council_tax=draw(money(3_000)),
        savings=draw(st.one_of(st.just(0.0), money(15_000))),
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
                    "is_blind": {YEAR: a["blind"]},
                }
                for variable, value in a["disability"].items():
                    person[variable] = {YEAR: value}
                people[name] = person
                names.append(name)
            benunits[f"b{i}_{k}"] = {"members": names}
            households[f"h{i}_{k}"] = {
                "members": names,
                "country": {YEAR: "ENGLAND"},
                "region": {YEAR: "NORTH_WEST"},
                "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
                "rent": {YEAR: fam["rent"]},
                "council_tax": {YEAR: fam["council_tax"]},
                "savings": {YEAR: fam["savings"]},
            }
    return {"people": people, "benunits": benunits, "households": households}


def grid(families):
    simulation = Simulation(situation=situation(families))
    shape = (len(families), len(PENSIONS))
    return {
        variable: np.asarray(simulation.calculate(variable, YEAR)).reshape(shape)
        for variable in [
            "household_net_income",
            "tv_licence",
            "minimum_guarantee",
            "guarantee_credit",
            "housing_benefit_eligible",
            "housing_benefit_applicable_amount",
            "council_tax_reduction_applicable_amount",
            "housing_benefit",
            "council_tax_benefit",
        ]
    }


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_pension_age_applicable_amounts_cover_the_minimum_guarantee(families):
    g = grid(families)
    for i, fam in enumerate(families):
        eligible = g["housing_benefit_eligible"][i].astype(bool)
        minimum_guarantee = g["minimum_guarantee"][i]
        hb = g["housing_benefit_applicable_amount"][i]
        ctr = g["council_tax_reduction_applicable_amount"][i]
        assert np.all(hb[eligible] >= minimum_guarantee[eligible] - 0.01), fam
        assert np.all(ctr >= minimum_guarantee - 0.01), fam


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_net_income_does_not_fall_where_guarantee_credit_ends(families):
    g = grid(families)
    net = g["household_net_income"] + g["tv_licence"]
    step = np.diff(net, axis=1)
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


@PROPERTY_SETTINGS
@given(
    st.lists(adult(), min_size=1, max_size=2),
    st.integers(18, 95),
)
def test_premiums_follow_the_pension_age_and_working_age_schedules(adults, age):
    people = {}
    for j, a in enumerate(adults):
        person = {
            "age": {YEAR: age if j == 0 else a["age"]},
            "is_blind": {YEAR: a["blind"]},
        }
        for variable, value in a["disability"].items():
            person[variable] = {YEAR: value}
        people[f"p{j}"] = person
    simulation = Simulation(
        situation={
            "people": people,
            "benunits": {"b": {"members": list(people)}},
            "households": {"h": {"members": list(people)}},
        }
    )

    def get(variable):
        return float(simulation.calculate(variable, YEAR)[0])

    pension_age = bool(simulation.calculate("is_SP_age", YEAR).any())
    premium = get("pension_age_severe_disability_premium")
    if pension_age:
        weekly_rate = float(
            simulation.tax_benefit_system.parameters(
                YEAR
            ).gov.dwp.pension_credit.guarantee_credit.severe_disability.addition
        )
        rates = premium / (weekly_rate * 52)
        assert min(abs(rates - k) for k in (0, 1, 2)) < 1e-6, rates
        assert (
            abs(premium - get("severe_disability_minimum_guarantee_addition")) < 0.005
        )
        expected = premium + get("carer_premium")
    else:
        assert premium == 0
        expected = sum(
            get(variable)
            for variable in [
                "disability_premium",
                "enhanced_disability_premium",
                "severe_disability_premium",
                "carer_premium",
            ]
        )
    assert abs(get("benefits_premiums") - expected) < 0.005
