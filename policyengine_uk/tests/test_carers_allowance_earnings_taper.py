"""The Budget 2026 Carer's Allowance earnings taper.

Budget 2026 (paragraph 6.13; costings page 16; Table 6.1, item 7) replaces
the withdrawal of Carer's Allowance in full above the weekly earnings limit
with a 100% taper on the earnings above it, in England and Wales, from a date
within 2030-31 (6 October 2030 until DWP confirms it). The tests read the
limit and the weekly rate from the parameter tree, so they hold whatever the
limit's projection (gov.dwp.carers_allowance.earnings_limit). Examples first,
then identities that hold for every input:

- in England and Wales from 2031-32 the weekly allowance is the rate less the
  earnings above the limit, floored at zero;
- the taper never pays less than the cliff edge it replaces;
- weekly earnings plus the allowance never fall as earnings rise: no cliff;
- Scotland (Carer Support Payment) and Northern Ireland are unchanged.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

TAPER = "gov.dwp.carers_allowance.earnings_taper"
FULL_YEAR = 2031
START_YEAR = 2030
# 6 October 2030 to 5 April 2031 is 182 of 2030-31's 365 days.
START_YEAR_SHARE = 182 / 365
WITHOUT_TAPER = {f"{TAPER}.applies": {str(year): 0 for year in (START_YEAR, FULL_YEAR)}}
REGIONS = ["NORTH_WEST", "WALES", "NORTHERN_IRELAND", "SCOTLAND"]
TAPER_REGIONS = ["NORTH_WEST", "WALES"]


def carer(weekly_earnings, year, region):
    return {
        "people": {
            "carer": {
                "age": {year: 45},
                "care_hours": {year: 40},
                "carers_allowance_earnings": {year: 52 * weekly_earnings},
            }
        },
        "benunits": {"benunit": {"members": ["carer"]}},
        "households": {"household": {"members": ["carer"], "region": {year: region}}},
    }


def weekly_allowance(weekly_earnings, year, region="NORTH_WEST", reform=None):
    sim = Simulation(situation=carer(weekly_earnings, year, region), reform=reform)
    return float(sim.calculate("carers_allowance_pre_couple_limit", year)[0]) / 52


def ca_parameters(year):
    sim = Simulation(situation=carer(0, year, "NORTH_WEST"))
    ca = sim.tax_benefit_system.parameters.gov.dwp.carers_allowance
    return ca.earnings_limit(f"{year}-04-30"), ca.rate(f"{year}-04-30")


def test_at_the_limit_the_full_rate_is_paid():
    limit, rate = ca_parameters(FULL_YEAR)
    assert weekly_allowance(limit, FULL_YEAR) == pytest.approx(rate, abs=0.01)


@pytest.mark.parametrize("region", TAPER_REGIONS)
def test_ten_pounds_over_the_limit_takes_ten_pounds_off(region):
    limit, rate = ca_parameters(FULL_YEAR)
    assert weekly_allowance(limit + 10, FULL_YEAR, region) == pytest.approx(
        rate - 10, abs=0.01
    )


def test_earnings_a_full_rate_over_the_limit_leave_nothing():
    limit, rate = ca_parameters(FULL_YEAR)
    assert weekly_allowance(np.ceil(limit + rate) + 1, FULL_YEAR) == 0


@pytest.mark.parametrize("region", ["NORTHERN_IRELAND", "SCOTLAND"])
def test_no_taper_outside_england_and_wales(region):
    limit, _ = ca_parameters(FULL_YEAR)
    assert weekly_allowance(limit + 10, FULL_YEAR, region) == 0


def test_no_taper_before_2030_31():
    limit, _ = ca_parameters(2029)
    assert weekly_allowance(limit + 10, 2029) == 0


def test_2030_31_carries_the_taper_for_the_weeks_from_6_october():
    limit, rate = ca_parameters(START_YEAR)
    assert weekly_allowance(limit + 10, START_YEAR) == pytest.approx(
        START_YEAR_SHARE * (rate - 10), abs=0.01
    )


def test_below_the_limit_2030_31_pays_the_full_rate():
    limit, rate = ca_parameters(START_YEAR)
    assert weekly_allowance(limit - 1, START_YEAR) == pytest.approx(rate, abs=0.01)


CASES = 24
STEP = 1.0
weekly = st.one_of(
    st.integers(min_value=0, max_value=400).map(float),
    st.floats(min_value=150, max_value=360),
)
cases = st.lists(weekly, min_size=CASES, max_size=CASES)


def situation():
    # The second half repeats the first with STEP more weekly earnings.
    n = 2 * CASES
    return {
        "people": {
            f"person_{i}": {"age": {FULL_YEAR: 45}, "care_hours": {FULL_YEAR: 40}}
            for i in range(n)
        },
        "benunits": {f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(n)},
        "households": {
            f"household_{i}": {
                "members": [f"person_{i}"],
                "region": {FULL_YEAR: REGIONS[i % len(REGIONS)]},
            }
            for i in range(n)
        },
    }


@pytest.fixture(scope="module")
def sims():
    return Simulation(situation=situation()), Simulation(
        situation=situation(), reform=WITHOUT_TAPER
    )


def run(sims, drawn):
    earnings = np.tile(np.array(drawn), 2)
    earnings[CASES:] += STEP
    results = []
    for sim in sims:
        sim.set_input("carers_allowance_earnings", FULL_YEAR, 52 * earnings)
        sim.reset_calculations()
        results.append(
            sim.calculate("carers_allowance_pre_couple_limit", FULL_YEAR).astype(float)
            / 52
        )
    regions = np.array([REGIONS[i % len(REGIONS)] for i in range(2 * CASES)])
    return earnings, regions, results[0], results[1]


SETTINGS = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(cases)
def test_the_allowance_is_the_rate_less_earnings_above_the_limit(sims, drawn):
    earnings, regions, law, _ = run(sims, drawn)
    limit, rate = ca_parameters(FULL_YEAR)
    expected = np.maximum(0, rate - np.maximum(0, earnings - limit))
    tapers = np.isin(regions, TAPER_REGIONS)
    # A penny for the disregarded fraction of a penny of weekly earnings.
    assert (np.abs(law - expected)[tapers] <= 0.011).all()


@SETTINGS
@given(cases)
def test_the_taper_never_pays_less_than_the_cliff_edge(sims, drawn):
    _, regions, law, cliff = run(sims, drawn)
    assert (law >= cliff - 1e-4).all()
    unchanged = ~np.isin(regions, TAPER_REGIONS)
    assert (np.abs(law - cliff)[unchanged] <= 1e-4).all()


@SETTINGS
@given(cases)
def test_earnings_plus_the_allowance_never_fall_as_earnings_rise(sims, drawn):
    earnings, regions, law, _ = run(sims, drawn)
    total = earnings + law
    tapers = np.isin(regions, TAPER_REGIONS)[:CASES]
    rise = total[CASES:] - total[:CASES]
    assert (rise[tapers] >= -0.011).all()


# Overlapping benefits come off only in the weeks the allowance is paid. A
# carer over the limit in 2030-31 is paid from 6 October 2030 only, so only
# that share of a weekly overlapping benefit reduces it.


def final_allowance(weekly_earnings, weekly_state_pension, year, region="NORTH_WEST"):
    situation = carer(weekly_earnings, year, region)
    person = situation["people"]["carer"]
    person["age"] = {year: 70}
    person["state_pension"] = {year: 52 * weekly_state_pension}
    sim = Simulation(situation=situation)
    return float(sim.calculate("carers_allowance", year)[0])


def test_2030_31_takes_overlapping_benefits_off_only_the_taper_weeks():
    # £250 a week is £46 over the £204 limit; £40 a week of State Pension.
    limit, rate = ca_parameters(START_YEAR)
    excess = 250 - limit
    expected = START_YEAR_SHARE * max(rate - excess - 40, 0) * 52
    assert final_allowance(250, 40, START_YEAR) == pytest.approx(expected, abs=0.05)


def test_full_taper_year_takes_off_the_whole_overlapping_benefit():
    limit, rate = ca_parameters(FULL_YEAR)
    excess = 250 - limit
    expected = max(rate - excess - 40, 0) * 52
    assert final_allowance(250, 40, FULL_YEAR) == pytest.approx(expected, abs=0.05)


def test_below_the_limit_2030_31_takes_off_the_whole_overlapping_benefit():
    limit, rate = ca_parameters(START_YEAR)
    expected = max(rate - 40, 0) * 52
    assert final_allowance(limit - 1, 40, START_YEAR) == pytest.approx(
        expected, abs=0.05
    )


overlap_cases = st.lists(
    st.tuples(weekly, st.floats(min_value=0, max_value=150)),
    min_size=CASES,
    max_size=CASES,
)


def overlap_situation():
    return {
        "people": {
            f"person_{i}": {"age": {START_YEAR: 70}, "care_hours": {START_YEAR: 40}}
            for i in range(CASES)
        },
        "benunits": {
            f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(CASES)
        },
        "households": {
            f"household_{i}": {
                "members": [f"person_{i}"],
                "region": {START_YEAR: REGIONS[i % len(REGIONS)]},
            }
            for i in range(CASES)
        },
    }


@pytest.fixture(scope="module")
def overlap_sim():
    return Simulation(situation=overlap_situation())


@SETTINGS
@given(overlap_cases)
def test_2030_31_allowance_is_the_weekly_overlap_rule_over_the_paid_weeks(
    overlap_sim, drawn
):
    earnings = np.array([e for e, _ in drawn])
    pension = np.array([p for _, p in drawn])
    overlap_sim.set_input("carers_allowance_earnings", START_YEAR, 52 * earnings)
    overlap_sim.set_input("state_pension", START_YEAR, 52 * pension)
    overlap_sim.reset_calculations()
    paid = overlap_sim.calculate("carers_allowance", START_YEAR).astype(float)
    above = overlap_sim.calculate(
        "carers_allowance_weekly_earnings_above_limit", START_YEAR
    ).astype(float)
    limit, rate = ca_parameters(START_YEAR)
    regions = np.array([REGIONS[i % len(REGIONS)] for i in range(CASES)])
    tapers = np.isin(regions, TAPER_REGIONS)
    # Weeks paid: all of them at or below the limit; above it, the taper
    # weeks in England and Wales and none elsewhere.
    share = np.where(above > 0, np.where(tapers, START_YEAR_SHARE, 0), 1)
    weekly = np.where(above > 0, np.maximum(0, rate - above), rate)
    expected = share * 52 * np.maximum(0, weekly - pension)
    # Scotland pays Carer Support Payment instead.
    england_wales_ni = regions != "SCOTLAND"
    assert (np.abs(paid - expected)[england_wales_ni] <= 0.05).all()
