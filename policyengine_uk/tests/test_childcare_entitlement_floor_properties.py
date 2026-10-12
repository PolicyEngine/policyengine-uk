"""How the universal, targeted and extended childcare entitlements combine.

Childcare Act 2016 s.1(6)(a) counts the childcare available under Childcare
Act 2006 s.7(1) (the universal 3-4 and targeted 2-year-old hours) towards the
working parent's 30 hours a week. DfE's statutory guidance (Early education
and childcare, valid from 1 April 2026, para A1.11 and "Amount of free
childcare for children of working parents") gives a child eligible for both
15 universal or Early Learning for 2-year-olds hours plus 15 working parent
hours. Sources fetched on 2026-10-07:
https://www.legislation.gov.uk/ukpga/2016/5/section/1
https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026

The model's extended hours parameter gives each child's working parent total
(30 a week for a 3- or 4-year-old, universal hours included), limited by the
child's own hours used and the family's maximum hours used. Invariants, for
randomly drawn families, each simulated twice (eligible and not):

1. Becoming eligible never lowers a family's childcare support (universal +
   targeted + extended), nor any child's.
2. Universal and targeted values do not depend on eligibility.
3. Each child's funded value equals an independent scalar reference:
   max(universal or targeted value, working parent total) when eligible, the
   universal or targeted value otherwise. So nothing is counted twice and no
   child falls below the universal or targeted hours.
4. A child's funded hours never exceed the larger of its universal or
   targeted hours and its working parent total, so never 30 hours a week
   plus the universal 15.
5. Raising the family's maximum hours used, or a child's own hours used,
   never lowers support.
6. A child counts as receiving the extended entitlement exactly when it has
   working parent hours beyond its universal or targeted hours.
7. The family's extended_childcare_entitlement equals the sum of its
   children's working parent amounts.
8. Statutory maximum: no child is funded for more than 30 hours in each of 38
   weeks (1,140 hours a year: Childcare Act 2016 s.1(1), SI 2022/1134 reg
   44(2)(b), guidance para A1.10), nor for more than 570 hours a year when
   the family is not eligible for the working parent hours (guidance paras
   A1.1 and A1.6), nor for more hours than it uses. These bounds are written
   from the law, not read from the model's parameters.
9. No child gets both universal and targeted hours, so its universal or
   targeted floor is at most 15 hours a week.
10. Outside England no child gets universal or working parent hours
    (Childcare Act 2006 s.7 and 2016 s.1(2)(b) are duties for England).

A further property runs the real eligibility test: raising the £100,000
income limit never lowers childcare support or household net income, and the
change in household net income equals the change in the three entitlements.
"""

import math
from unittest.mock import patch

from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.tax_benefit_system import system

_PROPERTY_SYSTEM = system.clone()
PROPERTY_SETTINGS = settings(
    max_examples=30,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
ENTITLEMENTS = (
    "universal_childcare_entitlement",
    "targeted_childcare_entitlement",
    "extended_childcare_entitlement_per_child",
)
# Statutory maxima in hours a year, written from the law (invariant 8).
WEEKS = 38
WORKING_PARENT_MAX_HOURS = 30 * WEEKS  # 1,140: SI 2022/1134 reg 44(2)(b)
UNIVERSAL_OR_TARGETED_MAX_HOURS = 570  # Guidance paras A1.1 and A1.6
HOURS_TOLERANCE = 0.01


def close(a, b):
    # Values are stored in single precision.
    return abs(a - b) <= 0.02 + 1e-6 * abs(b)


child = st.fixed_dictionaries(
    {
        "age": st.sampled_from([0, 0.5, 0.75, 1, 2, 2.5, 3, 4, 4.9, 5, 6]),
        "hours_used": st.sampled_from([0, 5, 10, 14.9, 15, 15.1, 20, 30, 45]),
        "looked_after": st.booleans(),
    }
)
family = st.fixed_dictionaries(
    {
        "children": st.lists(child, min_size=1, max_size=3),
        "cap": st.sampled_from([0, 5, 10, 14.9, 15, 15.1, 18, 20, 30, 40, 60]),
        "claims_universal": st.booleans(),
        "targeted": st.booleans(),
        "england": st.sampled_from([True, True, True, False]),
    }
)
years = st.sampled_from([2024, 2025, 2026])


def new_simulation(**kwargs):
    """A Simulation on a clone of the already loaded tax-benefit system."""
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=_PROPERTY_SYSTEM.clone,
    ):
        return Simulation(**kwargs)


def simulate(families, year, eligible, cap_bump=0, hours_bump=0):
    """One Simulation: each family appears once per value in ``eligible``."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for copy, is_eligible in enumerate(eligible):
        for i, f in enumerate(families):
            members = []
            for j, c in enumerate(f["children"]):
                name = f"c{copy}_{i}_{j}"
                situation["people"][name] = {
                    "age": {year: c["age"]},
                    "max_free_entitlement_hours_used": {
                        year: c["hours_used"] + hours_bump
                    },
                    "is_looked_after_by_local_authority": {year: c["looked_after"]},
                }
                members.append(name)
            situation["benunits"][f"b{copy}_{i}"] = {
                "members": members,
                "extended_childcare_entitlement_eligible": {year: is_eligible},
                "targeted_childcare_entitlement_eligible": {year: f["targeted"]},
                "would_claim_universal_childcare": {year: f["claims_universal"]},
                "maximum_extended_childcare_hours_usage": {year: f["cap"] + cap_bump},
            }
            situation["households"][f"h{copy}_{i}"] = {
                "members": members,
                "country": {year: "ENGLAND" if f["england"] else "WALES"},
            }
    sim = new_simulation(situation=situation)
    values = {v: [float(x) for x in sim.calculate(v, year)] for v in ENTITLEMENTS}
    values["receiving"] = [
        bool(x) for x in sim.calculate("is_child_receiving_extended_childcare", year)
    ]
    # The family amount, repeated on each child.
    values["family_extended"] = [
        float(x)
        for x in sim.calculate("extended_childcare_entitlement", year, map_to="person")
    ]
    return values


def split(values, families, n_copies):
    """values[var][person] -> [copy][family][child] dicts."""
    out, k = [], 0
    for _ in range(n_copies):
        copy = []
        for f in families:
            children = []
            for _ in f["children"]:
                children.append({v: values[v][k] for v in values})
                k += 1
            copy.append(children)
        out.append(copy)
    return out


def reference(c, f, year, eligible):
    """Each child's funded value, written from s.1(6) and para A1.11."""
    p = system.parameters(f"{year}-01-01").gov.dfe
    age = c["age"]
    rate = float(p.childcare_funding_rate.calc(age))
    weeks = p.weeks_per_year
    under_school_age = age < 5
    in_england = f["england"]
    universal_hours = (
        min(c["hours_used"] * weeks, p.universal_childcare_entitlement.hours)
        if in_england and f["claims_universal"] and 3 <= age < 5
        else 0
    )
    targeted_hours = (
        min(
            c["hours_used"] * weeks,
            p.targeted_childcare_entitlement.hours_entitlement
            * float(p.targeted_childcare_entitlement.age_eligibility.calc(age)),
        )
        if f["targeted"]
        else 0
    )
    floor = (universal_hours + targeted_hours) * rate
    qualifying = (
        in_england
        and under_school_age
        and not c["looked_after"]
        and age >= p.extended_childcare_entitlement.young_child_minimum_age
    )
    weekly = (
        min(
            float(p.extended_childcare_entitlement.hours.calc(age)),
            c["hours_used"],
            f["cap"],
        )
        if qualifying
        else 0
    )
    working_parent_total = weekly * weeks * rate
    total = max(floor, working_parent_total) if eligible else floor
    return floor, total, working_parent_total


def funded(child_values):
    return sum(child_values[v] for v in ENTITLEMENTS)


def assert_statutory_bounds(c, f, year, eligible, child_values):
    """Invariants 8 to 10 for one child, eligible or not."""
    rate = float(
        system.parameters(f"{year}-01-01").gov.dfe.childcare_funding_rate.calc(c["age"])
    )
    hours = funded(child_values) / rate
    context = (year, f, c, eligible, child_values, hours)
    # 8. At most 30 hours a week over 38 weeks; at most the universal or
    # targeted 570 hours without the working parent hours; and never more
    # hours than the child uses.
    limit = WORKING_PARENT_MAX_HOURS if eligible else UNIVERSAL_OR_TARGETED_MAX_HOURS
    assert hours <= limit + HOURS_TOLERANCE, context
    assert hours <= WEEKS * max(c["hours_used"], 0) + HOURS_TOLERANCE, context
    # 9. Never both universal and targeted hours.
    assert not (
        child_values["universal_childcare_entitlement"] > 0
        and child_values["targeted_childcare_entitlement"] > 0
    ), context
    # 10. No universal or working parent hours outside England. (These tests
    # supply targeted eligibility as an input, which bypasses its own England
    # condition.)
    if not f["england"]:
        assert child_values["universal_childcare_entitlement"] == 0, context
        assert child_values["extended_childcare_entitlement_per_child"] == 0, context


@PROPERTY_SETTINGS
@given(years, st.lists(family, min_size=1, max_size=5))
@example(
    2026,
    [
        # The documented loss case before the fix: a 3-year-old whose family
        # uses 10 hours a week (reg 2022/1134 eligibility gave 380 extended
        # hours in place of 570 universal ones).
        {
            "children": [{"age": 3, "hours_used": 30, "looked_after": False}],
            "cap": 10,
            "claims_universal": True,
            "targeted": False,
            "england": True,
        },
        # A 2-year-old eligible for both targeted and working parent hours.
        {
            "children": [{"age": 2, "hours_used": 30, "looked_after": False}],
            "cap": 30,
            "claims_universal": True,
            "targeted": True,
            "england": True,
        },
    ],
)
def test_becoming_eligible_never_lowers_childcare_support(year, families):
    values = simulate(families, year, eligible=[False, True])
    not_eligible, eligible = split(values, families, 2)
    for f, before, after in zip(families, not_eligible, eligible):
        # 1. Never lower, for the family or any child.
        assert sum(map(funded, after)) >= sum(map(funded, before)) - 0.02, f
        # 7. The family amount is the sum of its children's amounts.
        for copy in (before, after):
            per_child = sum(c["extended_childcare_entitlement_per_child"] for c in copy)
            assert close(copy[0]["family_extended"], per_child), (year, f, copy)
        for c, b, a in zip(f["children"], before, after):
            assert funded(a) >= funded(b) - 0.02, (year, f, c, b, a)
            # 8-10. Statutory maximum, no double floor, England only.
            assert_statutory_bounds(c, f, year, False, b)
            assert_statutory_bounds(c, f, year, True, a)
            # 2. Universal and targeted do not depend on eligibility.
            for v in (
                "universal_childcare_entitlement",
                "targeted_childcare_entitlement",
            ):
                assert close(a[v], b[v]), (year, f, c, v, b, a)
            assert b["extended_childcare_entitlement_per_child"] == 0
            # 3. Matches the scalar reference.
            floor, total_after, working_parent_total = reference(c, f, year, True)
            _, total_before, _ = reference(c, f, year, False)
            assert close(funded(b), total_before), (year, f, c, b, total_before)
            assert close(funded(a), total_after), (year, f, c, a, total_after)
            # 4. Never both added in full.
            assert funded(a) <= max(floor, working_parent_total) + 0.02
            # 6. Receiving means hours beyond the universal or targeted ones.
            top_up = a["extended_childcare_entitlement_per_child"]
            assert a["receiving"] == (top_up > 0), (year, f, c, a)
            assert a["receiving"] == (working_parent_total > floor + 0.01), (
                year,
                f,
                c,
                a,
                floor,
                working_parent_total,
            )
            assert not b["receiving"]


@PROPERTY_SETTINGS
@given(years, st.lists(family, min_size=1, max_size=5), st.sampled_from([1, 5, 15]))
def test_more_hours_used_never_lowers_childcare_support(year, families, bump):
    lower = split(simulate(families, year, eligible=[True]), families, 1)[0]
    for cap_bump, hours_bump in ((bump, 0), (0, bump)):
        raised = simulate(
            families, year, eligible=[True], cap_bump=cap_bump, hours_bump=hours_bump
        )
        higher = split(raised, families, 1)[0]
        for f, lo, hi in zip(families, lower, higher):
            for c, a, b in zip(f["children"], lo, hi):
                assert funded(b) >= funded(a) - 0.02, (year, f, c, bump, a, b)
                # 8. However many hours are used, never above 30 a week.
                used = {**c, "hours_used": c["hours_used"] + hours_bump}
                assert_statutory_bounds(used, f, year, True, b)


# The real eligibility route: a working couple with a child, one parent's
# adjusted net income either side of £100,000, with and without the limit.
INCOME_LIMIT = "gov.dfe.extended_childcare_entitlement.income.limit"
couple = st.tuples(
    st.sampled_from([30_000, 99_000, 100_000, 100_001, 150_000]),
    st.sampled_from([20_000, 60_000]),
    st.lists(st.sampled_from([0, 1, 2, 3, 4]), min_size=1, max_size=2),
    st.sampled_from([0, 10, 15, 20, 30]),
)


@settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(couple)
def test_raising_the_income_limit_never_lowers_support_or_income(h):
    high, low, ages, cap = h
    year = 2026
    people = {
        "parent1": {
            "age": {year: 35},
            "employment_income": {year: high},
            "is_parent": {year: True},
        },
        "parent2": {
            "age": {year: 35},
            "employment_income": {year: low},
            "is_parent": {year: True},
        },
    }
    for j, age in enumerate(ages):
        people[f"child{j}"] = {"age": {year: age}}
    members = list(people)
    situation = {
        "people": people,
        "benunits": {
            "bu": {
                "members": members,
                "maximum_extended_childcare_hours_usage": {year: cap},
            }
        },
        "households": {"hh": {"members": members, "country": {year: "ENGLAND"}}},
    }
    base = new_simulation(situation=situation)
    reform = new_simulation(situation=situation, reform={INCOME_LIMIT: math.inf})

    def total(sim, variable):
        return float(sim.calculate(variable, year).sum())

    support = ENTITLEMENTS
    before = sum(total(base, v) for v in support)
    after = sum(total(reform, v) for v in support)
    assert after >= before - 0.02, h
    d_income = total(reform, "household_net_income") - total(
        base, "household_net_income"
    )
    assert d_income >= -0.05, h
    assert abs(d_income - (after - before)) <= 0.05, h
