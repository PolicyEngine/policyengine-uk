"""Properties of the income-related ESA and income-based JSA work conditions.

Welfare Reform Act 2007 Sch 1 para 6(1)(e) and (f) and Jobseekers Act 1995
ss.1(2)(e), 1(2B)(b) and 3(1)(e) bar an award when the claimant, or the other
member of the couple, is engaged in remunerative work. For every family:

- esa_income_eligible and jsa_income_eligible equal a family-by-family
  reading of the law (legacy_award_work_reference), and is_jsa_joint_claim_couple
  equals the reading of s.1(4) and JSA Regs reg 3A(1);
- more hours or more pay for anyone never makes a family eligible, because
  the conditions only ever bar a claim;
- caring never ends an ESA award (a carer partner is not treated as in
  remunerative work, ESA Regs reg 43(2)(c)) and never matters for JSA (the
  JSA regulations have no carer exception);
- when the claimant or partner reports the award, adding a member outside
  the family (a non-dependent adult, with any award and any work) never
  changes either screen.

The reference covers employees with no other income and pay within the basic
rate band. Roles are given explicitly (is_claimant_or_partner). Each example
builds many families in one simulation, in separate households and benefit
units.
"""

import numpy as np
from hypothesis import HealthCheck, event, given, settings
from hypothesis import strategies as st

from legacy_award_work_reference import esa_screen, jsa_joint_claim, jsa_screen
from policyengine_uk import Simulation

# 0, 15, 16, 20, 23, 24 and 40 hours a week.
HOURS = [0, 0, 780, 832, 1_040, 1_196, 1_248, 2_080]
# £0, £20 (the lower limit), £21, £100, £195.50 (the 2025-26 higher limit),
# £196, £203.50 (2026-27), £204 and £300 a week.
PAY = [0, 0, 1_040, 1_092, 5_200, 10_166, 10_192, 10_582, 10_608, 15_600]


@st.composite
def adults(draw, outside_family=False):
    pay = draw(st.sampled_from(PAY))
    adult = {
        "age": draw(
            st.one_of(
                st.integers(18 if not outside_family else 20, 64), st.integers(70, 90)
            )
        ),
        "esa_income_reported": draw(st.sampled_from([0, 0, 3_000])),
        "jsa_income_reported": draw(st.sampled_from([0, 0, 3_000])),
        "hours_worked": draw(st.sampled_from(HOURS)),
        "employment_income": pay,
        "employee_pension_contributions": (
            draw(st.sampled_from([0, 0, 520])) if pay <= 12_570 else 0
        ),
        "receives_carer_benefit": draw(st.booleans()),
        "care_hours": draw(st.sampled_from([0, 0, 35])),
    }
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


SETTINGS = settings(
    max_examples=40,
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
    joint = sim.calculate("is_jsa_joint_claim_couple", year)
    if esa.any():
        event("some ESA award passes")
    if jsa.any():
        event("some JSA award passes")
    parameters = sim.tax_benefit_system.parameters(year)
    for i, (couple, children, others, capital) in enumerate(units):
        expected_joint = jsa_joint_claim(couple, bool(children), year, parameters)
        assert joint[i] == expected_joint, units[i]
        assert esa[i] == esa_screen(couple, others, capital, parameters), units[i]
        assert jsa[i] == jsa_screen(
            couple, others, capital, expected_joint, parameters
        ), units[i]


@st.composite
def more_work(draw, family):
    """The same family with more hours or more pay for anyone."""
    couple, children, others, capital = family

    def more(adult):
        adult = dict(adult)
        adult["hours_worked"] += draw(st.sampled_from([0, 52, 260, 832, 1_248]))
        adult["employment_income"] += draw(st.sampled_from([0, 52, 1_040, 5_200]))
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
