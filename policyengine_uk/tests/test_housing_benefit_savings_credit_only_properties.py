"""Housing Benefit where the Pension Credit award is savings credit only.

HB(SPC) Regs 2006 (SI 2006/214) reg 27 (NI: SR 2006/406 reg 25): the
authority uses the Secretary of State's assessment of income and capital for
the award, modified to take account of "the amount of the savings credit
payable" (reg 27(4)(a)) and the other items reg 27(4) lists; Housing
Benefit's own income rules, including tariff income, do not apply to it (reg
27(5)); and the £16,000 limit applies to the Secretary of State's capital (reg
27(6)).

Before this change Housing Benefit counted none of the savings credit. On a
rise in private pension savings credit fell by 40% of the rise in net income,
Housing Benefit by 65% of it and council tax reduction by 20%, so a family
lost more than it gained. A single person aged 88 on Attendance Allowance
whose private pension rose from £9,000 to £9,500 in 2026 lost £13.29 of net
income, excluding the TV licence. Counting the savings credit, Housing
Benefit falls by 65% of the rise net of the savings credit withdrawn, 39% in
all, and the combined withdrawal is 99% (91% once council tax reduction also
counts the savings credit, PolicyEngine/policyengine-uk#1909).

Invariants, for single people and couples aged 80 or over (so State Pension
age was reached before April 2016 and savings credit is possible), who rent
from the council in England, Wales or Scotland and have no children, carers
or earnings, with private pension on a £250 grid:

1. Monotonicity: on every step on which the family has a savings-credit-only
   award at both ends, household net income, excluding the TV licence, does
   not fall.
2. Boundary: on the step where savings credit ends, household net income does
   not fall, excluding the TV licence, the Winter Fuel Payment and the
   Scottish Pension Age Winter Heating Payment, which the model makes depend
   on receiving Pension Credit (the free licence at 75, the Scottish payment's
   Pension Credit rates, and the Winter Fuel Payment above £35,000 of taxable
   income). Housing Benefit switches from the Secretary of State's figure to
   its own rules there.
3. Differential: a savings-credit-only family's Housing Benefit income is the
   Pension Credit income, recomputed here from pensions, income tax and the
   deemed income on savings, plus the savings credit, less the earnings
   disregard; its tariff income is zero and its capital is its savings. Other
   families keep the Housing Benefit rules: zero income with a guarantee
   credit, otherwise pensions less income tax plus tariff income less the
   earnings disregard.

Carers are not drawn.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
# Wide enough that every drawn family starts with a guarantee credit or savings
# credit and ends with no Pension Credit: a couple both on Attendance Allowance
# with no State Pension leaves savings credit at about £35,000.
PENSIONS = np.arange(0, 40_001, 250)
PROPERTY_SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Local authorities without a modelled local council tax reduction scheme, so
# each country's national scheme applies.
COUNTRIES = {
    "ENGLAND": "MAIDSTONE",
    "WALES": "CARDIFF",
    "SCOTLAND": "GLASGOW_CITY",
}
DISABILITY = st.sampled_from(
    [
        {},
        {},
        {"aa_category": "LOWER"},
        {"aa_category": "HIGHER"},
        {"dla_sc_category": "MIDDLE"},
        {"pip_dl_category": "ENHANCED"},
    ]
)
# Pension Credit deemed income and pension-age Housing Benefit tariff income:
# £1 a week for each £500, or part, of capital over £10,000.
CAPITAL_THRESHOLD = 10_000
CAPITAL_STEP = 500
WEEKS = 52


def money(low, high):
    return st.floats(low, high, allow_nan=False, allow_infinity=False)


@st.composite
def adult(draw):
    return dict(
        # Aged 80 or over in 2026, so State Pension age was reached before
        # 6 April 2016 and savings credit is possible. (The model tests this
        # against the current State Pension age of 66, so in 2026 it admits
        # only people aged 77 or over and excludes qualifying people aged 76
        # or under.)
        age=draw(st.integers(80, 100)),
        disability=draw(DISABILITY),
        blind=draw(st.booleans()),
        # At most £10,000 each, so a couple without disability starts below
        # the top of the savings credit range (about £21,500 of income).
        state_pension=draw(money(0, 10_000)),
    )


@st.composite
def family(draw):
    return dict(
        adults=[draw(adult()) for _ in range(draw(st.integers(1, 2)))],
        country=draw(st.sampled_from(sorted(COUNTRIES))),
        rent=draw(money(3_000, 12_000)),
        council_tax=draw(money(500, 3_000)),
        savings=draw(st.one_of(st.just(0.0), money(0, 16_000))),
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
                "country": {YEAR: fam["country"]},
                "local_authority": {YEAR: COUNTRIES[fam["country"]]},
                "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
                "rent": {YEAR: fam["rent"]},
                "council_tax": {YEAR: fam["council_tax"]},
                "savings": {YEAR: fam["savings"]},
            }
    return {"people": people, "benunits": benunits, "households": households}


BENUNIT_VARIABLES = [
    "guarantee_credit",
    "savings_credit",
    "pension_credit",
    "minimum_guarantee",
    "housing_benefit",
    "housing_benefit_applicable_income",
    "housing_benefit_applicable_income_disregard",
    "housing_benefit_assessable_capital",
    "housing_benefit_tariff_income",
    "council_tax_benefit",
]
HOUSEHOLD_VARIABLES = [
    "household_net_income",
    "tv_licence",
    "winter_fuel_allowance",
    "pawhp",
]


def grid(families):
    simulation = Simulation(situation=situation(families))
    shape = (len(families), len(PENSIONS))
    values = {
        variable: np.asarray(simulation.calculate(variable, YEAR)).reshape(shape)
        for variable in BENUNIT_VARIABLES + HOUSEHOLD_VARIABLES
    }
    for variable in ["state_pension", "private_pension_income", "income_tax"]:
        values[variable] = np.asarray(
            simulation.calculate(variable, YEAR, map_to="benunit")
        ).reshape(shape)
    # An award of savings credit only: Pension Credit is paid and none of it
    # is guarantee credit.
    values["savings_credit_only"] = (values["pension_credit"] > 0) & (
        values["guarantee_credit"] <= 0
    )
    values["guarantee_credit_paid"] = (values["pension_credit"] > 0) & (
        values["guarantee_credit"] > 0
    )
    return values


def describe(fam, g, i, k):
    return (
        fam,
        f"private pension {PENSIONS[k]} -> {PENSIONS[k + 1]}",
        f"savings credit {g['savings_credit'][i, k]:.2f} -> "
        f"{g['savings_credit'][i, k + 1]:.2f}",
        f"HB {g['housing_benefit'][i, k]:.2f} -> {g['housing_benefit'][i, k + 1]:.2f}",
        f"CTR {g['council_tax_benefit'][i, k]:.2f} -> "
        f"{g['council_tax_benefit'][i, k + 1]:.2f}",
    )


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_net_income_rises_with_private_pension_on_savings_credit_only(families):
    g = grid(families)
    net = g["household_net_income"] + g["tv_licence"]
    step = np.diff(net, axis=1)
    sc_only = g["savings_credit_only"]
    both_ends = sc_only[:, :-1] & sc_only[:, 1:]
    # Every family is on savings credit only for part of the grid.
    assert both_ends.any(axis=1).all(), families
    for i, fam in enumerate(families):
        for k in np.flatnonzero(both_ends[i]):
            assert step[i, k] >= -0.01, (
                *describe(fam, g, i, k),
                f"net income change {step[i, k]:.2f}",
            )


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_net_income_does_not_fall_where_savings_credit_ends(families):
    g = grid(families)
    net = (
        g["household_net_income"]
        + g["tv_licence"]
        - g["winter_fuel_allowance"]
        - g["pawhp"]
    )
    step = np.diff(net, axis=1)
    ends = g["savings_credit_only"][:, :-1] & (g["pension_credit"][:, 1:] <= 0)
    assert ends.any(axis=1).all(), families
    for i, fam in enumerate(families):
        for k in np.flatnonzero(ends[i]):
            assert step[i, k] >= -0.01, (
                *describe(fam, g, i, k),
                f"net income change {step[i, k]:.2f}",
            )


def deemed_income(capital):
    steps = np.ceil(np.maximum(0, capital - CAPITAL_THRESHOLD) / CAPITAL_STEP)
    return steps * WEEKS


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_income_follows_the_route_for_the_award(families):
    g = grid(families)
    savings = np.array([fam["savings"] for fam in families])[:, None]
    capital_income = deemed_income(savings)
    pensions_after_tax = (
        g["state_pension"] + g["private_pension_income"] - g["income_tax"]
    )
    disregard = g["housing_benefit_applicable_income_disregard"]
    sc_only = g["savings_credit_only"]
    gc_paid = g["guarantee_credit_paid"]
    other = ~sc_only & ~gc_paid
    income = g["housing_benefit_applicable_income"]
    capital = np.broadcast_to(savings, income.shape)
    capital_income = np.broadcast_to(capital_income, income.shape)

    # Savings credit only: the Secretary of State's income (pensions after
    # tax plus deemed income on savings) plus the savings credit paid.
    pension_credit_income = pensions_after_tax + capital_income
    expected = np.maximum(0, pension_credit_income + g["pension_credit"] - disregard)
    assert np.allclose(income[sc_only], expected[sc_only], atol=0.01)
    assert np.all(g["housing_benefit_tariff_income"][sc_only] == 0)
    assert np.allclose(
        g["housing_benefit_assessable_capital"][sc_only], capital[sc_only], atol=0.01
    )
    # Guarantee credit: the whole income is disregarded.
    assert np.all(income[gc_paid] == 0)
    # Otherwise the Housing Benefit rules, with tariff income on savings.
    expected = np.maximum(0, pensions_after_tax + capital_income - disregard)
    assert np.allclose(income[other], expected[other], atol=0.01)
    assert np.allclose(
        g["housing_benefit_tariff_income"][other], capital_income[other], atol=0.01
    )


def single_pensioner(**person):
    return {
        "people": {"pensioner": person},
        "benunits": {"benunit": {"members": ["pensioner"]}},
        "households": {
            "household": {
                "members": ["pensioner"],
                "country": {YEAR: "ENGLAND"},
                "local_authority": {YEAR: "MAIDSTONE"},
                "region": {YEAR: "NORTH_WEST"},
                "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
                "rent": {YEAR: 11_117.22},
                "council_tax": {YEAR: 2_782.16},
                "savings": {YEAR: 0.0},
            }
        },
    }


def test_attendance_allowance_case_no_longer_loses_net_income():
    # The counterexample that found the gap: single, aged 88, blind, on
    # Attendance Allowance at the higher rate, State Pension 11,609.88.
    def calculate(private_pension):
        simulation = Simulation(
            situation=single_pensioner(
                age={YEAR: 88},
                is_blind={YEAR: True},
                aa_category={YEAR: "HIGHER"},
                state_pension={YEAR: 11_609.88},
                private_pension_income={YEAR: private_pension},
            )
        )
        return {
            variable: float(simulation.calculate(variable, YEAR).sum())
            for variable in [
                "savings_credit",
                "housing_benefit_applicable_income",
                "housing_benefit_applicable_income_disregard",
                "housing_benefit",
                "household_net_income",
                "tv_licence",
            ]
        }

    before, after = calculate(9_000), calculate(9_500)
    # 400 more after income tax; savings credit falls by 0.4 x 183.22 to nil.
    assert abs(before["savings_credit"] - 73.29) < 0.01
    assert after["savings_credit"] == 0
    # 19,001.90 of Pension Credit income + 73.29 of savings credit, less the
    # earnings disregard, which applies on both routes.
    assert (
        abs(
            before["housing_benefit_applicable_income"]
            + before["housing_benefit_applicable_income_disregard"]
            - 19_075.19
        )
        < 0.01
    )
    # 0.65 x (19,401.90 - 19,075.19) = 212.36.
    assert abs(before["housing_benefit"] - after["housing_benefit"] - 212.36) < 0.01
    # Excluding the TV licence (free for over-75s on Pension Credit), net
    # income rises; on main it fell by 13.29.
    change = (after["household_net_income"] + after["tv_licence"]) - (
        before["household_net_income"] + before["tv_licence"]
    )
    assert change > 0


def test_savings_credit_only_award_counts_the_frozen_savings_credit():
    # A savings credit rate rise raises the reform's savings credit from
    # 718.62 to 1,029.89, but the Pension Credit freeze keeps paying the
    # baseline 718.62, and that is the savings credit payable.
    data = single_pensioner(
        age={YEAR: 80},
        state_pension={YEAR: 11_000},
        private_pension_income={YEAR: 2_000},
    )
    data["benunits"]["benunit"]["housing_benefit_applicable_income_disregard"] = {
        YEAR: 0
    }
    period = f"{YEAR}-01-01.{YEAR}-12-31"
    rate_rise = {"gov.dwp.pension_credit.savings_credit.rate.phase_in": {period: 0.8}}
    frozen = Simulation(
        situation=data,
        reform={**rate_rise, "gov.contrib.freeze_pension_credit": {period: True}},
    )
    unfrozen = Simulation(situation=data, reform=rate_rise)
    assert abs(frozen.calculate("savings_credit", YEAR)[0] - 1_029.89) < 0.01
    assert abs(frozen.calculate("pension_credit", YEAR)[0] - 718.62) < 0.01
    assert frozen.calculate("in_receipt_of_savings_credit_only", YEAR)[0]
    # 12,914 of Pension Credit income + 718.62 paid.
    frozen_income = frozen.calculate("housing_benefit_applicable_income", YEAR)[0]
    assert abs(frozen_income - 13_632.62) < 0.01
    # Without the freeze the higher savings credit is paid and counted.
    unfrozen_income = unfrozen.calculate("housing_benefit_applicable_income", YEAR)[0]
    assert abs(unfrozen_income - 13_943.89) < 0.01
