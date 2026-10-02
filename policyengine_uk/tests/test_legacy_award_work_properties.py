"""Properties of the income-related ESA and income-based JSA work conditions.

Welfare Reform Act 2007 Sch 1 para 6(1)(e) and (f) and Jobseekers Act 1995
ss.1(2)(e) and 3(1)(e) (with JSA Regs 1996 reg 3E for joint-claim couples)
bar an award when the claimant, or the other member of the couple, is engaged
in remunerative work. For every family:

- esa_income_eligible and jsa_income_eligible equal a family-by-family
  reading of the law (legacy_award_work_reference);
- more hours or more pay for anyone never makes a family eligible, in the
  years tested (2025 and 2026). Before 6 April 2024 reg 99(3)(a) took a
  fixed Class 2 deduction once profit reached a threshold, so £1 more
  profit could lower net earnings; that intended cliff is a YAML case;
- caring never ends an ESA award (a carer partner is not treated as in
  remunerative work, ESA Regs reg 43(2)(c)) and never matters for JSA (the
  JSA regulations have no exception for carers doing unrelated paid work);
- when the claimant or partner reports the award, adding a member outside
  the family (a non-dependent adult, with any award and any work) never
  changes either screen.

Adults are employees (pay within the basic rate band), self-employed (a
profit within the Class 4 upper limit) or employees with a self-employment
loss, aged either side of state pension age, where National Insurance stops.
Some also receive statutory sick, maternity or paternity pay, which is not
earnings (ESA Regs reg 95(2)(b)); they have no other income. This is the
scope the reference covers. Roles are given explicitly
(is_claimant_or_partner). Each example builds many families in one
simulation, in separate households and benefit units.
"""

import numpy as np
from hypothesis import HealthCheck, event, given, settings
from hypothesis import strategies as st

from legacy_award_work_reference import esa_screen, esa_weekly_earnings, jsa_screen
from policyengine_uk import Simulation

# 0, 15, 16, 20, 23, 24 and 40 hours a week.
HOURS = [0, 0, 780, 832, 1_040, 1_196, 1_248, 2_080]
# £0, £20 (the lower limit), £21, £100, £195.50 (the 2025-26 higher limit),
# £196, £203.50 (2026-27), £204 and £300 a week.
PAY = [0, 0, 1_040, 1_092, 5_200, 10_166, 10_192, 10_582, 10_608, 15_600]
# Profits around the limits once reg 99's notional tax and Class 4 come off,
# and £13,200, which needs half a £5,900 pension premium to fall within them.
PROFIT = [1_040, 5_200, 10_166, 10_300, 13_200, 15_600]
# Payments an employer makes for sickness or leave, which are not earnings
# (reg 95(2)(b)) but which the shared taxable pay and Class 1 bases include.
STATUTORY_PAY = [
    None,
    None,
    None,
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
]


@st.composite
def adults(draw, outside_family=False):
    kind = draw(
        st.sampled_from(
            ["employee", "employee", "self_employed", "mixed", "loss", "big_loss"]
        )
    )
    min_age = 18 if not outside_family else 20
    # Ages either side of state pension age, where National Insurance stops.
    age = draw(st.one_of(st.integers(min_age, 64), st.integers(70, 90)))
    pay = 0 if kind == "self_employed" else draw(st.sampled_from(PAY))
    adult = {
        "age": age,
        "esa_income_reported": draw(st.sampled_from([0, 0, 3_000])),
        "jsa_income_reported": draw(st.sampled_from([0, 0, 3_000])),
        "hours_worked": draw(st.sampled_from(HOURS)),
        "employment_income": pay,
        "employee_pension_contributions": (
            draw(st.sampled_from([0, 0, 520])) if pay > 0 else 0
        ),
        "receives_carer_benefit": draw(st.booleans()),
        "care_hours": draw(st.sampled_from([0, 0, 35])),
    }
    if kind in ("self_employed", "mixed"):
        adult["self_employment_income"] = draw(st.sampled_from(PROFIT))
    if kind in ("self_employed", "mixed", "employee"):
        # Personal pension contributions go to the profit when there is one,
        # and to the pay otherwise.
        adult["personal_pension_contributions"] = draw(
            st.sampled_from([0, 0, 520, 5_900])
        )
    if kind == "loss":
        adult["self_employment_income"] = -1_000
    elif kind == "big_loss":
        # A loss larger than the pay.
        adult["self_employment_income"] = -20_000
    statutory_pay = draw(st.sampled_from(STATUTORY_PAY))
    if statutory_pay is not None:
        adult[statutory_pay] = draw(st.sampled_from([1_040, 3_000]))
    if outside_family:
        adult["current_education"] = "NOT_IN_EDUCATION"
    return adult


@st.composite
def families(draw):
    """A claimant, an optional partner, children, an optional child placed by a
    local authority, an optional member outside the family, and capital."""
    couple = [draw(adults())]
    if draw(st.booleans()):
        couple.append(draw(adults()))
    children = [
        {"age": draw(st.integers(0, 15))} for _ in range(draw(st.integers(0, 2)))
    ]
    if draw(st.integers(0, 4)) == 0:
        children.append(
            {
                "age": draw(st.integers(0, 15)),
                "is_looked_after_by_local_authority": True,
            }
        )
    others = [draw(adults(outside_family=True))] if draw(st.booleans()) else []
    capital = draw(st.sampled_from([0, 0, 6_250, 16_000, 20_000]))
    return couple, children, others, capital


def situation(units, year):
    people, benunits, households = {}, {}, {}
    for i, (couple, children, others, capital) in enumerate(units):
        members = (
            [(m, True) for m in couple]
            + [(m, False) for m in children]
            + [(m, False) for m in others]
        )
        names = []
        for j, (inputs, claimant_or_partner) in enumerate(members):
            name = f"p{i}_{j}"
            people[name] = {k: {year: v} for k, v in inputs.items()}
            people[name]["is_claimant_or_partner"] = {year: claimant_or_partner}
            people[name]["is_parent"] = {year: claimant_or_partner and bool(children)}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "esa_income_assessable_capital": {year: capital},
            "jsa_income_assessable_capital": {year: capital},
        }
        households[f"h{i}"] = {"members": names}
    return {"people": people, "benunits": benunits, "households": households}


def label(units):
    adults_ = [a for couple, _, others, _ in units for a in couple + others]
    for program in ["esa", "jsa"]:
        if any(a[f"{program}_income_reported"] for a in adults_):
            event(f"someone reports {program}")
    if any(len(couple) == 2 and not children for couple, children, _, _ in units):
        event("couple without children")
    if any(
        c.get("is_looked_after_by_local_authority") for _, cs, _, _ in units for c in cs
    ):
        event("placed child")
    if any(others for *_, others, _ in units):
        event("member outside the family")
    if any(a.get("self_employment_income", 0) > 0 for a in adults_):
        event("self-employed")
    if any(a.get("self_employment_income", 0) < 0 for a in adults_):
        event("self-employment loss beside pay")
    if any(
        a.get("self_employment_income", 0) > 0 and a.get("employment_income", 0) > 0
        for a in adults_
    ):
        event("pay and profit together")
    if any(
        a.get("employment_income", 0) > 0
        and any(a.get(name, 0) > 0 for name in STATUTORY_PAY if name)
        for a in adults_
    ):
        event("statutory pay beside pay")


SETTINGS = settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
FAMILIES = st.lists(families(), min_size=1, max_size=10)
YEARS = st.sampled_from([2025, 2026])


@SETTINGS
@given(FAMILIES, YEARS)
def test_screens_match_a_family_by_family_reading(units, year):
    label(units)
    sim = Simulation(situation=situation(units, year))
    esa = sim.calculate("esa_income_eligible", year)
    jsa = sim.calculate("jsa_income_eligible", year)
    if esa.any():
        event("some ESA award passes")
    if jsa.any():
        event("some JSA award passes")
    earnings = sim.calculate("esa_exempt_work_earnings", year)
    parameters = sim.tax_benefit_system.parameters(year)
    start = 0
    for i, (couple, children, others, capital) in enumerate(units):
        assert esa[i] == esa_screen(couple, others, capital, parameters), units[i]
        assert jsa[i] == jsa_screen(couple, others, capital, parameters), units[i]
        members = couple + children + others
        for j, member in enumerate(members):
            if member in children:
                continue
            expected = esa_weekly_earnings(member, parameters)
            assert abs(earnings[start + j] - expected) < 0.01, (member, expected)
        start += len(members)


@st.composite
def more_work(draw, family):
    """The same family with more hours or more pay for anyone."""
    couple, children, others, capital = family

    def more(adult):
        adult = dict(adult)
        adult["hours_worked"] += draw(st.sampled_from([0, 52, 260, 832, 1_248]))
        adult["employment_income"] += draw(st.sampled_from([0, 52, 1_040, 5_200]))
        if adult.get("self_employment_income", 0) > 0:
            adult["self_employment_income"] += draw(st.sampled_from([0, 52, 1_040]))
        return adult

    return [more(a) for a in couple], children, [more(a) for a in others], capital


@SETTINGS
@given(FAMILIES, YEARS, st.data())
def test_more_work_never_makes_a_family_eligible(units, year, data):
    more = [data.draw(more_work(family)) for family in units]
    sim = Simulation(situation=situation(units + more, year))
    n = len(units)
    for variable in ["esa_income_eligible", "jsa_income_eligible"]:
        eligible = sim.calculate(variable, year)
        if (eligible[:n] & ~eligible[n:]).any():
            event(f"more work removed {variable}")
        assert not (eligible[n:] & ~eligible[:n]).any(), variable


@SETTINGS
@given(FAMILIES, YEARS)
def test_caring_never_ends_esa_and_never_matters_for_jsa(units, year):
    def caring(family):
        couple, children, others, capital = family
        return (
            [dict(a, receives_carer_benefit=True) for a in couple],
            children,
            [dict(a, receives_carer_benefit=True) for a in others],
            capital,
        )

    def not_caring(family):
        couple, children, others, capital = family
        return (
            [dict(a, receives_carer_benefit=False, care_hours=0) for a in couple],
            children,
            [dict(a, receives_carer_benefit=False, care_hours=0) for a in others],
            capital,
        )

    n = len(units)
    sim = Simulation(
        situation=situation(
            [not_caring(u) for u in units] + [caring(u) for u in units], year
        )
    )
    esa = sim.calculate("esa_income_eligible", year)
    jsa = sim.calculate("jsa_income_eligible", year)
    if (esa[n:] & ~esa[:n]).any():
        event("a carer partner kept an ESA award")
    assert not (esa[:n] & ~esa[n:]).any()
    assert (jsa[:n] == jsa[n:]).all()


@SETTINGS
@given(FAMILIES, YEARS, st.data())
def test_member_outside_the_family_never_changes_the_couples_screen(units, year, data):
    extras = [data.draw(adults(outside_family=True)) for _ in units]
    without = [
        (couple, children, [], capital) for couple, children, _, capital in units
    ]
    with_extra = [
        (couple, children, [extra], capital)
        for (couple, children, _, capital), extra in zip(units, extras)
    ]
    n = len(units)
    sim = Simulation(situation=situation(without + with_extra, year))
    flags = sim.calculate("is_claimant_or_partner", year)
    sizes = [len(c) + len(ch) + len(o) for c, ch, o, _ in without + with_extra]
    ends = np.cumsum(sizes)
    for variable, reported in [
        ("esa_income_eligible", "esa_income_reported"),
        ("jsa_income_eligible", "jsa_income_reported"),
    ]:
        eligible = sim.calculate(variable, year)
        for i, (couple, *_rest) in enumerate(without):
            assert not flags[ends[n + i] - 1]
            if any(a[reported] > 0 for a in couple):
                assert eligible[i] == eligible[n + i], (variable, units[i], extras[i])
