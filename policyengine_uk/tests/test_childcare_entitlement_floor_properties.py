"""How the universal, targeted and extended childcare entitlements combine.

Childcare Act 2016 s.1(6)(a) counts the childcare available under Childcare
Act 2006 s.7(1) (the universal 3-4 and targeted 2-year-old hours) towards the
working parent's 30 hours a week. DfE's statutory guidance (Early education
and childcare, valid from 1 April 2026, para A1.11 and "Amount of free
childcare for children of working parents") gives a child eligible for both
15 universal or Early Learning for 2-year-olds hours plus 15 working parent
hours. Sources fetched on 2026-10-07:
https://www.legislation.gov.uk/ukpga/2016/5/section/1
https://www.legislation.gov.uk/uksi/2014/2147/regulation/3/made
https://www.legislation.gov.uk/uksi/2014/2147/regulation/4/made
https://www.legislation.gov.uk/uksi/2023/1330/pdfs/uksi_20231330_en.pdf
https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026

The model's extended hours parameter gives each child's working parent total
(30 a week for a 3- or 4-year-old, universal hours included), limited by the
child's own hours used and the family's maximum hours used. Invariants, for
randomly drawn families, each simulated twice (eligible and not):

1. Becoming eligible never lowers a family's childcare support (universal +
   targeted + extended), nor any child's.
2. Legal universal and targeted eligibility does not depend on standalone
   take-up. A participating child's first funded hours, up to 15 a week, go
   to the applicable base programme even when its standalone flag is false.
3. Each child's funded value equals an independent scalar reference, term by
   term: max(claimed standalone value, working parent total) in the terms
   the child is old enough for when eligible (invariant 12), the claimed
   standalone value otherwise. Programme allocations count the legally
   available base hours first, preserving that total.
4. In no term do a child's funded hours exceed the larger of its universal
   or targeted hours and its working parent hours, so never 30 hours a week
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
   A1.1 and A1.6). Under-threes get at most 570 annual hours before September
   2025: two-year-olds qualify from April 2024 and children from nine months
   from September 2024 (SI 2023/1330 reg 2). No child gets more hours than it
   uses. These bounds are written from the law, not read from the model's
   parameters; annual simulations still evaluate the schedule at January.
9. No child gets both universal and targeted hours, so its universal or
   targeted floor is at most 15 hours a week.
10. Outside England no child gets universal or working parent hours
    (Childcare Act 2006 s.7 and 2016 s.1(2)(b) are duties for England).
11. No universal or working parent hours in the terms after a child starts
    school: a reception place meets both duties (guidance footnotes 7 and 17,
    paras A4.8 and C.6). Reception starts in the September following the
    fourth birthday (guidance C.5), unless the start is deferred.
12. Working parent hours start with the first 1 January, 1 April or 1
    September after the child attains the minimum age (SI 2022/1134 reg
    27(1)(a)); the year's terms begin on 1 April, 1 September and 1 January,
    a third of the year each. A whole age is the middle of the year of age,
    so the child was born on 6 April; a fractional age is exact on 6 October.

A further property runs the real eligibility test: raising the £100,000
income limit never lowers childcare support or household net income, and the
change in household net income equals the change in the three entitlements.
"""

import math
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import load_parameter_file

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


def months_later(day, months):
    """The same day of the month ``months`` calendar months later."""
    index = day.year * 12 + day.month - 1 + months
    return date(index // 12, index % 12 + 1, day.day)


def born_on(age, year):
    """A whole age is the middle of the year of age; a fractional one is
    exact on 6 October. The drawn ages are whole months, apart from 4.9: in
    November either way, years from every boundary these tests use."""
    months_old = 12 * age if age != int(age) else 12 * age + 6
    return months_later(date(year, 10, 6), -round(months_old))


def year_terms(year):
    return (date(year, 4, 1), date(year, 9, 1), date(year + 1, 1, 1))


def term_share(age, year, minimum_age):
    """Invariant 12: the share of the year's terms after the child attains
    the minimum age."""
    attains = months_later(born_on(age, year), round(12 * minimum_age))
    return sum(attains < start for start in year_terms(year)) / 3


def before_school(c, year):
    """Invariant 11: the share of the year's terms before the child starts
    reception, in the September following its fourth birthday."""
    if c.get("deferred"):
        return 1
    born = born_on(c["age"], year)
    starts_school = date(born.year + 4 + (born.month >= 9), 9, 1)
    return sum(start < starts_school for start in year_terms(year)) / 3


child = st.fixed_dictionaries(
    {
        "age": st.sampled_from([0, 0.5, 0.75, 1, 2, 2.5, 3, 4, 4.9, 5, 6]),
        "hours_used": st.sampled_from([0, 5, 10, 14.9, 15, 15.1, 20, 30, 45]),
        "looked_after": st.booleans(),
        # A deferred start keeps the year's hours.
        "deferred": st.sampled_from([False, False, False, True]),
    }
)
family = st.fixed_dictionaries(
    {
        "children": st.lists(child, min_size=1, max_size=3),
        "cap": st.sampled_from([0, 5, 10, 14.9, 15, 15.1, 18, 20, 30, 40, 60]),
        "claims_universal": st.booleans(),
        "claims_targeted": st.booleans(),
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
                if c.get("deferred"):
                    situation["people"][name]["early_years_school_start_deferred"] = {
                        year: True
                    }
                members.append(name)
            situation["benunits"][f"b{copy}_{i}"] = {
                "members": members,
                "extended_childcare_entitlement_eligible": {year: is_eligible},
                "targeted_childcare_entitlement_eligible": {year: f["targeted"]},
                "would_claim_universal_childcare": {year: f["claims_universal"]},
                "would_claim_targeted_childcare": {year: f["claims_targeted"]},
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
    values["universal_eligible"] = [
        bool(x) for x in sim.calculate("universal_childcare_entitlement_eligible", year)
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
    # The terms before the child starts school: none of these hours after it.
    school = before_school(c, year)
    universal_hours = (
        min(c["hours_used"] * weeks, p.universal_childcare_entitlement.hours)
        if in_england and 3 <= age < 5 and school > 0
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
    universal_value = universal_hours * rate * school
    targeted_value = targeted_hours * rate
    floor = (
        universal_value * f["claims_universal"] + targeted_value * f["claims_targeted"]
    )
    minimum_age = p.extended_childcare_entitlement.young_child_minimum_age
    share = term_share(age, year, minimum_age)
    qualifying = (
        in_england
        and under_school_age
        and not c["looked_after"]
        and school > 0
        and share > 0
    )
    weekly = (
        min(
            # The hours for its age, or for the minimum age if it reaches
            # that later in the year.
            float(p.extended_childcare_entitlement.hours.calc(max(age, minimum_age))),
            c["hours_used"],
            f["cap"],
        )
        if qualifying
        else 0
    )
    # A child starting school is years past the minimum age, so the terms it
    # is old enough for include every term before it starts school.
    working_parent_total = weekly * weeks * rate * school if eligible else 0
    # In the terms the child is old enough for: the larger of the claimed
    # standalone value and the working parent total, with legal eligibility,
    # independent of standalone take-up, determining which programme funds
    # the first hours. In the other terms: the claimed standalone value.
    participating = max(floor, working_parent_total)
    total = share * participating + (1 - share) * floor
    allocations = {
        "universal_childcare_entitlement": share * min(universal_value, participating)
        + (1 - share) * universal_value * f["claims_universal"],
        "targeted_childcare_entitlement": share * min(targeted_value, participating)
        + (1 - share) * targeted_value * f["claims_targeted"],
    }
    allocations["extended_childcare_entitlement_per_child"] = total - sum(
        allocations.values()
    )
    return floor, total, participating, allocations


def funded(child_values):
    return sum(child_values[v] for v in ENTITLEMENTS)


def statutory_max_hours(c, instant, eligible):
    """Age/date maximum from the law, without reading model parameters."""
    instant = date.fromisoformat(instant)
    # SI 2023/1330 reg 2(8)(a), commenced by reg 1(2)(b), expands
    # under-three hours from 570 to 1,140 on 1 September 2025.
    if not eligible or (c["age"] < 3 and instant < date(2025, 9, 1)):
        return UNIVERSAL_OR_TARGETED_MAX_HOURS
    return WORKING_PARENT_MAX_HOURS


def assert_statutory_maximum(c, f, instant, eligible, hours):
    """Independent annual and actual-use bounds, including rollout dates."""
    context = (instant, f, c, eligible, hours)
    assert hours <= statutory_max_hours(c, instant, eligible) + HOURS_TOLERANCE, context
    assert hours <= WEEKS * max(c["hours_used"], 0) + HOURS_TOLERANCE, context


def assert_statutory_bounds(c, f, instant, eligible, child_values):
    """Invariants 8 to 10 for one child, eligible or not."""
    rate = float(
        system.parameters(instant).gov.dfe.childcare_funding_rate.calc(c["age"])
    )
    hours = funded(child_values) / rate
    context = (instant, f, c, eligible, child_values, hours)
    # 8. At most 30 hours a week over 38 weeks; at most the universal or
    # targeted 570 hours without the working parent hours; and never more
    # hours than the child uses. Under-threes have a separate 15-hour limit
    # before September 2025, independent of the model's hours schedule.
    assert_statutory_maximum(c, f, instant, eligible, hours)
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
    # Legally universal children can have only the additional 15 weekly
    # hours classified as extended, irrespective of standalone take-up.
    if f["england"] and 3 <= c["age"] < 5:
        extended_hours = child_values["extended_childcare_entitlement_per_child"] / rate
        assert extended_hours <= UNIVERSAL_OR_TARGETED_MAX_HOURS + HOURS_TOLERANCE, (
            context
        )


@pytest.mark.parametrize(
    "instant, age, limit",
    [
        ("2024-03-31", 2, 570),
        ("2024-04-01", 2, 570),
        ("2024-08-31", 0.75, 570),
        ("2024-09-01", 0.75, 570),
        ("2025-08-31", 0.75, 570),
        ("2025-08-31", 2, 570),
        ("2025-09-01", 0.75, 1_140),
        ("2025-09-01", 2, 1_140),
        ("2025-08-31", 3, 1_140),
    ],
)
def test_statutory_maximum_at_rollout_boundaries(instant, age, limit):
    """The independent assertion rejects excessive hours without a simulation."""
    c = {"age": age, "hours_used": 45, "looked_after": False}
    f = {"england": True, "targeted": False}
    assert statutory_max_hours(c, instant, eligible=True) == limit
    assert_statutory_maximum(c, f, instant, eligible=True, hours=limit)
    with pytest.raises(AssertionError):
        assert_statutory_maximum(c, f, instant, eligible=True, hours=limit + 1)


@pytest.mark.parametrize(
    "instant, age, weekly_hours",
    [
        ("2024-04-01", 2, 15),
        ("2024-09-01", 2, 15),
        ("2025-08-31", 1, 15),
        ("2025-08-31", 2, 15),
        ("2025-09-01", 1, 30),
        ("2025-09-01", 2, 30),
        ("2025-08-31", 3, 30),
        ("2025-09-01", 3, 30),
    ],
)
def test_working_parent_hours_schedule_at_rollout_boundaries(
    instant, age, weekly_hours
):
    """Check source dates before the model annualises its parameter tree.

    Annual simulations evaluate January; the processed tree therefore retains
    15 hours throughout 2025. The source scale keeps September's 30-hour change.
    The existing age schedule models the September 2024 expansion to
    nine-month-olds from January 2025; changing that approximation is separate.
    """
    hours_scale = load_parameter_file(
        str(
            Path(__file__).parents[1]
            / "parameters/gov/dfe/extended_childcare_entitlement/hours.yaml"
        ),
        "extended_childcare_hours",
    )
    hours = float(hours_scale(instant).calc(age))
    assert hours == weekly_hours
    c = {"age": age, "hours_used": 45, "looked_after": False}
    f = {"england": True, "targeted": False}
    assert_statutory_maximum(c, f, instant, eligible=True, hours=hours * WEEKS)


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
            "claims_targeted": True,
            "targeted": False,
            "england": True,
        },
        # A 2-year-old eligible for both targeted and working parent hours.
        {
            "children": [{"age": 2, "hours_used": 30, "looked_after": False}],
            "cap": 30,
            "claims_universal": True,
            "claims_targeted": True,
            "targeted": True,
            "england": True,
        },
    ],
)
@example(
    2026,
    [
        {
            "children": [
                {"age": age, "hours_used": 45, "looked_after": False}
                for age in (1, 2, 3)
            ],
            "cap": 60,
            "claims_universal": True,
            "claims_targeted": True,
            "targeted": True,
            "england": True,
        },
    ],
)
@example(
    2026,
    [
        {
            "children": [
                {"age": age, "hours_used": hours, "looked_after": False}
                for age, hours in ((2, 10), (3, 10), (4, 30))
            ],
            "cap": 30,
            "claims_universal": False,
            "claims_targeted": False,
            "targeted": True,
            "england": True,
        },
    ],
)
@example(
    2026,
    [
        # A 4-year-old starting reception in September (born on 6 April, so
        # funded for the summer term), one whose start is deferred, and a
        # 2-year-old sibling.
        {
            "children": [
                {
                    "age": age,
                    "hours_used": 30,
                    "looked_after": False,
                    "deferred": deferred,
                }
                for age, deferred in ((4, False), (4, True), (2, False))
            ],
            "cap": 30,
            "claims_universal": True,
            "claims_targeted": True,
            "targeted": False,
            "england": True,
        },
    ],
)
@example(
    2026,
    [
        # Nine months old on 6 October (eligible from the spring term), and
        # whole ages 0 (born 6 April, nine months old on 6 January: no term)
        # and 1 (every term).
        {
            "children": [
                {"age": age, "hours_used": 45, "looked_after": False}
                for age in (0.75, 0, 1)
            ],
            "cap": 60,
            "claims_universal": True,
            "claims_targeted": True,
            "targeted": False,
            "england": True,
        },
    ],
)
@example(
    2024,
    [
        # Two from April 2024: 2-year-olds born on 6 April qualify from
        # September, alongside targeted hours claimed on their own or not.
        {
            "children": [
                {"age": age, "hours_used": 30, "looked_after": False}
                for age in (2, 2.5, 1)
            ],
            "cap": 30,
            "claims_universal": True,
            "claims_targeted": claims_targeted,
            "targeted": True,
            "england": True,
        }
        for claims_targeted in (True, False)
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
            school = before_school(c, year)
            legal_universal = f["england"] and 3 <= c["age"] < 5 and school > 0
            assert a["universal_eligible"] == b["universal_eligible"] == legal_universal
            # 11. A school place, not funded hours, once the child starts
            # school: at most the terms before it.
            rate = float(
                system.parameters(f"{year}-01-01").gov.dfe.childcare_funding_rate.calc(
                    c["age"]
                )
            )
            for copy in (a, b):
                universal_hours = copy["universal_childcare_entitlement"] / rate
                assert universal_hours <= (
                    school * UNIVERSAL_OR_TARGETED_MAX_HOURS + HOURS_TOLERANCE
                ), (year, f, c, copy)
                assert (
                    universal_hours
                    + copy["extended_childcare_entitlement_per_child"] / rate
                    <= school * WORKING_PARENT_MAX_HOURS + HOURS_TOLERANCE
                ), (year, f, c, copy)
            # 8-10. Statutory maximum, no double floor, England only.
            assert_statutory_bounds(c, f, f"{year}-01-01", False, b)
            assert_statutory_bounds(c, f, f"{year}-01-01", True, a)
            assert b["extended_childcare_entitlement_per_child"] == 0
            # 2-3. Legal base hours fund participating children first,
            # even with false standalone flags. Each programme and the
            # combined total match the independent allocation reference.
            floor, total_after, participating, expected_after = reference(
                c, f, year, True
            )
            _, total_before, _, expected_before = reference(c, f, year, False)
            for actual, expected in ((a, expected_after), (b, expected_before)):
                for variable in ENTITLEMENTS:
                    assert close(actual[variable], expected[variable]), (
                        year,
                        f,
                        c,
                        variable,
                        actual,
                        expected,
                    )
            assert close(funded(b), total_before), (year, f, c, b, total_before)
            assert close(funded(a), total_after), (year, f, c, a, total_after)
            # 4. Never both added in full, even in the terms with working
            # parent hours.
            assert funded(a) <= participating + 0.02
            # 6. Receiving means hours beyond the universal or targeted ones.
            top_up = a["extended_childcare_entitlement_per_child"]
            assert a["receiving"] == (top_up > 0), (year, f, c, a)
            assert a["receiving"] == (
                expected_after["extended_childcare_entitlement_per_child"] > 0.01
            ), (
                year,
                f,
                c,
                a,
                floor,
                participating,
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
                assert_statutory_bounds(used, f, f"{year}-01-01", True, b)


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
