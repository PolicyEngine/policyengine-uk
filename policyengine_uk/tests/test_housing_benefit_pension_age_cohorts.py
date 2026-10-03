"""Pension-age Housing Benefit personal allowances by when State Pension age
was attained.

The Housing Benefit (Persons who have attained the qualifying age for state
pension credit) Regulations 2006 (SI 2006/214) Sch 3 para 1, as amended by SI
2021/188 from 1 April 2021 (Northern Ireland: SR 2006/406 Sch 4 para 1): a
single claimant or lone parent who attained pensionable age before 1 April
2021 gets the higher allowance in (1)(b), one who attained it on or after gets
(1)(c); a couple gets (2)(b) where one or both members attained it before, and
(2)(c) where both attained it on or after.

Invariants, for any pension-age single person or couple in any year:

1. Differential: the pension-age personal allowance in
   housing_benefit_applicable_amount is the higher rate exactly when a member's
   attainment day, read from the statute day by day
   (test_state_pension_age.reference_attainment_day), is before 1 April 2021,
   and the lower rate otherwise.
2. Bounds: the lower rate is below the higher rate in every year, including
   uprated years, and lone parents get the single rates.
3. Monotonicity: among pension-age single people of one sex in one year, an
   earlier date of birth never gives a lower allowance.
4. Before April 2021 there was one pension-age rate, which every pension-age
   unit gets.
5. The lower rates and the cutoff equal the statute's table for every year
   2021-22 to 2026-27 (hard-coded below from legislation.gov.uk).
6. Council Tax Reduction: England's pensioner scheme has the same split and
   amounts (SI 2012/2885 Sch 2 para 1, amended by SI 2021/29), so its
   allowance equals Housing Benefit's; the Scottish and Welsh schemes have
   one pension-age rate, the higher one.
"""

from datetime import date, timedelta

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system
from test_state_pension_age import grid_months, reference_attainment_day

CUTOFF = date(2021, 4, 1)
YEARS = list(range(2019, 2031))
P = system.parameters.gov.dwp.housing_benefit.allowances


def rates(year: int, couple: bool) -> tuple:
    """(higher, lower) weekly pension-age allowance; lower is None before the
    cutoff took effect."""
    node = P.couple if couple else P.single
    at = f"{year}-06-01"
    return node.aged(at), node.aged_from_cutoff(at)


def build(units: list, year: int, region: str = "LONDON") -> Simulation:
    """Each unit is a list of (birth, male). Units are eligible with no
    premiums, so the applicable amount is 52 times the personal allowance."""
    people, benunits = {}, {}
    mid_year = grid_months(date(year, 10, 6))
    for u, members in enumerate(units):
        names = []
        for k, (birth, male) in enumerate(members):
            age_in_months = mid_year - grid_months(birth)
            age = int(age_in_months // 12)
            name = f"u{u}p{k}"
            people[name] = {
                "age": {year: age},
                "months_since_last_birthday": {year: age_in_months - 12 * age},
                "is_male": {year: male},
            }
            names.append(name)
        benunits[f"u{u}"] = {
            "members": names,
            "housing_benefit_eligible": {year: True},
            "benefits_premiums": {year: 0},
        }
    return Simulation(
        situation={
            "people": people,
            "benunits": benunits,
            "households": {"h": {"members": list(people), "region": {year: region}}},
        }
    )


def at_pension_age(members: list, year: int) -> bool:
    mid_year = date(year, 10, 6)
    return any(reference_attainment_day(b, m) <= mid_year for b, m in members)


def expected_allowance(members: list, year: int) -> float:
    higher, lower = rates(year, couple=len(members) == 2)
    attained = [reference_attainment_day(b, m) for b, m in members]
    if lower is None or any(day < CUTOFF for day in attained):
        return higher
    return lower


def check(units: list, year: int) -> np.ndarray:
    """Invariant 1 for every unit with a member over State Pension age."""
    amount = build(units, year).calculate("housing_benefit_applicable_amount", year)
    weekly = amount / 52
    wrong = [
        (members, weekly[i], expected_allowance(members, year))
        for i, members in enumerate(units)
        if at_pension_age(members, year)
        and abs(weekly[i] - expected_allowance(members, year)) > 0.005
    ]
    assert not wrong, wrong[:10]
    return weekly


BIRTHS = [date(1938, 1, 1) + timedelta(days=d) for d in range(0, 23 * 366, 5)]
EDGES = [date(1955, 4, 1) + timedelta(days=shift) for shift in range(-3, 4)]


@pytest.mark.parametrize("year", YEARS)
def test_single_allowance_matches_statute_for_every_birth_date(year):
    """Invariants 1, 3 and 4 for single people born every fifth day from 1938
    and either side of 1 April 1955, the birthday that reaches 66 on the
    cutoff."""
    births = sorted(set(BIRTHS) | set(EDGES))
    for male in (True, False):
        units = [[(birth, male)] for birth in births]
        weekly = check(units, year)
        eligible = [weekly[i] for i, u in enumerate(units) if at_pension_age(u, year)]
        assert all(a >= b - 1e-6 for a, b in zip(eligible, eligible[1:]))
        if year < CUTOFF.year:
            assert np.allclose(eligible, rates(year, couple=False)[0])


@pytest.mark.parametrize("year", range(2021, 2041))
def test_lower_rates_are_below_higher_rates(year):
    """Invariant 2, including years uprated past the last published rate."""
    for couple in (False, True):
        higher, lower = rates(year, couple)
        assert lower < higher
    at = f"{year}-06-01"
    assert P.lone_parent.aged_from_cutoff(at) == P.single.aged_from_cutoff(at)


MEMBER = st.tuples(
    st.dates(min_value=date(1930, 1, 1), max_value=date(1962, 12, 31)),
    st.booleans(),
)


@settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(
    units=st.lists(st.lists(MEMBER, min_size=1, max_size=2), min_size=1, max_size=25),
    year=st.sampled_from(YEARS),
)
def test_any_single_or_couple_follows_the_cohort_rule(units, year):
    """Invariant 1 for random single people and couples, including couples
    where only one member is over State Pension age."""
    check(units, year)


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(
    units=st.lists(st.lists(MEMBER, min_size=1, max_size=2), min_size=1, max_size=20),
    year=st.sampled_from(YEARS),
    region=st.sampled_from(["LONDON", "NORTH_WEST", "SCOTLAND", "WALES"]),
)
def test_council_tax_reduction_splits_only_in_england(units, year, region):
    """Invariant 6 for random single people and couples."""
    sim = build(units, year, region)
    hb = sim.calculate("housing_benefit_applicable_amount", year) / 52
    ctr = sim.calculate("council_tax_reduction_applicable_amount", year) / 52
    for i, members in enumerate(units):
        if not at_pension_age(members, year):
            continue
        if region in ("SCOTLAND", "WALES"):
            expected = rates(year, couple=len(members) == 2)[0]
        else:
            expected = hb[i]
        assert abs(ctr[i] - expected) < 0.005, (members, region, ctr[i], expected)


# SI 2006/214 Sch 3 para 1(1)(c) and (2)(c), weekly: inserted by SI 2021/188 reg
# 2(3) from 1 April 2021, then set by the Up-rating Orders SI 2022/292,
# 2023/316, 2024/242, 2025/295 and 2026/148 (legislation.gov.uk point-in-time
# texts at 11 April 2022, 10 April 2023, 8 April 2024, 7 April 2025 and the
# current text).
STATUTE_LOWER_RATES = {
    2021: (177.10, 270.30),
    2022: (182.60, 278.70),
    2023: (201.05, 306.85),
    2024: (218.15, 332.95),
    2025: (227.10, 346.60),
    2026: (238.00, 363.25),
}


@pytest.mark.parametrize("year", sorted(STATUTE_LOWER_RATES))
def test_lower_rates_and_cutoff_match_the_statute(year):
    """Invariant 5."""
    single, couple = STATUTE_LOWER_RATES[year]
    at = f"{year}-06-01"
    assert P.single.aged_from_cutoff(at) == pytest.approx(single, abs=1e-6)
    assert P.lone_parent.aged_from_cutoff(at) == pytest.approx(single, abs=1e-6)
    assert P.couple.aged_from_cutoff(at) == pytest.approx(couple, abs=1e-6)
    assert P.pension_age_cutoff(at) == 20210401
