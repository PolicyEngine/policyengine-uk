"""Weekly earnings above the Carer's Allowance earnings limit, in exact pence.

carers_allowance_weekly_earnings_above_limit spreads net earnings over 52
weeks (Computation of Earnings Regulations 1996 regs. 8(1)(b)(iii) and
11(1)(a)), disregards the fraction of a penny that leaves (reg. 5), and gives
how far the whole pence a week exceed the limit (ICA Regulations 1976 reg.
8(1)). Two things read it: the gainful-employment test, which asks whether
there is any excess, and the Budget 2026 earnings taper, which takes
taper.rate (100%) of the excess off the weekly rate. So the amount of the
excess matters as well as its sign.

Annual earnings of A whole pence, against a limit of L pounds and a weekly
rate of R pounds, have an excess of E = max(0, A // 52 - 100 x L) pence a
week. Under the taper (applied by reform in each year from 2020-21, so every
limit since then is tested with it), for a carer in England caring 40 hours:

1. The excess is exact: E pence, recovered exactly from its float32 value,
   and the person is gainfully employed exactly when E > 0.
2. The award is the rate less the excess: 52 x max(0, 100 x R - E) pence a
   year, to within a float32 step of the annual award. (The rates after the
   last legislated one are the model's uprated projections, which need not
   be whole pence.)
3. It never pays more than the full rate.
4. It never goes negative.
5. It falls by at most £1 for each £1 of weekly earnings above the limit:
   comparing any two carers, the weekly award differs by no more than their
   excesses do.
6. At or under the limit it is the full rate.
"""

import math

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.pence import stored_pence

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

WEEKS = 52
FIRST_YEAR = 2020
# The last year the parameter tree lists a limit for, including any years
# the model projects after the last legislated limit.
HORIZON = max(
    int(value.instant_str[:4])
    for value in system.parameters.gov.dwp.carers_allowance.earnings_limit.values_list
)
YEARS = list(range(FIRST_YEAR, HORIZON + 1))
# The taper in every year, so that it reads each limit since 2020-21.
WITH_TAPER = {
    "gov.dwp.carers_allowance.earnings_taper.applies": {str(year): 1 for year in YEARS}
}


def _limit_and_rate_pence(year):
    """The limit, in whole pence, and the weekly rate, in pence, which a
    projected year may give with a fraction of a penny."""
    ca = system.parameters(f"{year}-04-30").gov.dwp.carers_allowance
    return round(ca.earnings_limit * 100), ca.rate * 100


def _within_a_step(award, expected):
    """Whether each annual ``award`` (pence) is ``expected`` (pence) to
    within a float32 step of the annual amount."""
    expected = np.asarray(expected, dtype=np.float64)
    step = np.spacing(np.float32(np.max(expected) / 100 + 1)).astype(float) * 100
    return np.abs(np.asarray(award) - expected) <= step


def _simulation(year, count):
    people = {
        f"carer_{i}": {"age": {year: 45}, "care_hours": {year: 40}}
        for i in range(count)
    }
    return Simulation(
        situation={
            "people": people,
            "benunits": {f"b{i}": {"members": [f"carer_{i}"]} for i in range(count)},
            "households": {
                f"h{i}": {
                    "members": [f"carer_{i}"],
                    "region": {year: "NORTH_WEST"},
                }
                for i in range(count)
            },
        },
        reform=WITH_TAPER,
    )


_SIMULATIONS = {}


def _run(year, annual_pence):
    """For carers with annual net earnings of ``annual_pence``: the excess
    and the award, each in exact pence (weekly and annual), and whether each
    is gainfully employed."""
    key = (year, len(annual_pence))
    if key not in _SIMULATIONS:
        _SIMULATIONS[key] = _simulation(year, len(annual_pence))
    simulation = _SIMULATIONS[key]
    simulation.set_input(
        "carers_allowance_earnings",
        year,
        np.array([p / 100 for p in annual_pence]),
    )
    simulation.reset_calculations()
    excess = stored_pence(
        simulation.calculate("carers_allowance_weekly_earnings_above_limit", year)
    )
    gainful = simulation.calculate("is_gainfully_employed_for_carers_allowance", year)
    award = simulation.calculate("carers_allowance", year).astype(np.float64) * 100
    return excess, gainful, award


def _expected(year, annual_pence):
    limit, rate = _limit_and_rate_pence(year)
    excess = np.array([max(0, p // WEEKS - limit) for p in annual_pence])
    award = WEEKS * np.maximum(0, rate - excess)
    return excess, award


# A carer exactly at the limit, and 1p, 2p and £1 a week over it.
STEPS = (0, 1, 2, 100)


@pytest.mark.parametrize("year", YEARS)
def test_a_penny_two_pence_and_a_pound_over_each_limit_taper_exactly(year):
    """Invariants 1, 2 and 6 at each limit from 2020-21 to the horizon: 52 x L
    + 52 x s pence a year (s pence a week over the limit), and 51p a year
    more, which reg. 5 disregards."""
    limit, rate = _limit_and_rate_pence(year)
    annual = [WEEKS * (limit + step) + extra for step in STEPS for extra in (0, 51)]
    excess, gainful, award = _run(year, annual)
    expected_excess = [step for step in STEPS for _ in (0, 51)]
    assert list(excess) == expected_excess, (year, limit)
    assert list(gainful) == [e > 0 for e in expected_excess], (year, limit)
    assert _within_a_step(award, [WEEKS * (rate - e) for e in expected_excess]).all(), (
        year,
        limit,
        list(award),
    )


@st.composite
def whole_pence_around_a_limit(draw):
    year = draw(st.sampled_from(YEARS))
    limit, rate = _limit_and_rate_pence(year)
    # The least number of pence a year that is over the limit, and the least
    # at which the taper leaves nothing.
    over = WEEKS * (limit + 1)
    nil = WEEKS * (limit + math.ceil(rate))
    near = st.one_of(
        st.integers(over - 3 * WEEKS, over + 3 * WEEKS),
        st.integers(nil - 3 * WEEKS, nil + 3 * WEEKS),
    )
    # Up to £131,071.99, below which float32 holds every whole-pence amount
    # to within half a penny.
    anywhere = st.integers(0, 2**17 * 100 - 1)
    pence = draw(st.lists(st.one_of(near, anywhere), min_size=40, max_size=40))
    return year, pence


@settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(case=whole_pence_around_a_limit())
# A penny a week over each limit #2541 affected, and a penny short of it.
@example(case=(2020, [WEEKS * 12_801 - 1, WEEKS * 12_801] * 20))
@example(case=(2022, [WEEKS * 13_201 - 1, WEEKS * 13_201] * 20))
@example(case=(2023, [WEEKS * 13_901 - 1, WEEKS * 13_901] * 20))
@example(case=(2024, [WEEKS * 15_101 - 1, WEEKS * 15_101] * 20))
def test_the_taper_follows_exact_pence(case):
    """Invariants 1 to 6 for whole-pence earnings anywhere, and near the
    points where the excess starts and where the taper leaves nothing."""
    year, pence = case
    _, rate = _limit_and_rate_pence(year)
    excess, gainful, award = _run(year, pence)
    expected_excess, expected_award = _expected(year, pence)
    # 1 and 2: exact.
    assert list(excess) == list(expected_excess), year
    assert list(gainful) == list(expected_excess > 0), year
    assert _within_a_step(award, expected_award).all(), year
    # A float32 step of the annual award, in pence a week.
    slack = np.spacing(np.float32(WEEKS * rate / 100)).astype(float) * 100 / WEEKS
    # 3 and 4: within the full rate and never negative.
    assert (award <= WEEKS * rate + WEEKS * slack).all(), year
    assert (award >= 0).all(), year
    # 5: between any two carers, the weekly award falls by no more than the
    # excess rises, and the award a week is at least the rate less the excess.
    weekly = award / WEEKS
    order = np.argsort(excess, kind="stable")
    fall = -np.diff(weekly[order])
    rise = np.diff(excess[order])
    assert (fall <= rise + 2 * slack).all(), year
    assert (rate - weekly <= excess + slack).all(), year
    # 6: the full rate at or under the limit.
    assert _within_a_step(award[excess == 0], WEEKS * rate).all(), year
