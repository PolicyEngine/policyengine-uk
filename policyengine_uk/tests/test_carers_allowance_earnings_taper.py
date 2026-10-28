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
- Scotland (Carer Support Payment) and Northern Ireland are unchanged;
- in 2030-31 the allowance paid is the weekly overlap rule over the weeks it
  is paid, for single carers and for couples caring for the same person, where
  the couple restriction picks a partner separately before and under the taper.
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


# A couple caring for the same person gets one award at a time. In 2030-31
# the couple restriction picks a partner separately for the weeks before the
# taper and the weeks under it.


def couple(head_weekly_earnings, partner_weekly_earnings, weekly_state_pension):
    def member(age, weekly_earnings):
        return {
            "age": {START_YEAR: age},
            "care_hours": {START_YEAR: 40},
            "carers_allowance_earnings": {START_YEAR: 52 * weekly_earnings},
            "state_pension": {START_YEAR: 52 * weekly_state_pension},
        }

    return {
        "people": {
            "head": member(71, head_weekly_earnings),
            "partner": member(70, partner_weekly_earnings),
        },
        "benunits": {
            "benunit": {
                "members": ["head", "partner"],
                "would_claim_uc": {START_YEAR: False},
            }
        },
        "households": {
            "household": {
                "members": ["head", "partner"],
                "country": {START_YEAR: "ENGLAND"},
            }
        },
    }


def test_2030_31_couple_keeps_the_partner_award_before_the_taper():
    # The head is £46 over the limit and gets the tapered allowance from
    # 6 October; the partner is under it and gets the full rate until then.
    limit, rate = ca_parameters(START_YEAR)
    sim = Simulation(situation=couple(limit + 46, limit - 4, 40))
    assert sim.calculate("partners_care_for_same_severely_disabled_person", START_YEAR)[
        0
    ]
    head, partner = sim.calculate("carers_allowance", START_YEAR).astype(float)
    assert head == pytest.approx(
        START_YEAR_SHARE * max(rate - 46 - 40, 0) * 52, abs=0.05
    )
    assert partner == pytest.approx(
        (1 - START_YEAR_SHARE) * max(rate - 40, 0) * 52, abs=0.05
    )


def test_a_couple_under_the_limit_gets_one_award_all_year():
    limit, rate = ca_parameters(START_YEAR)
    sim = Simulation(situation=couple(limit - 4, limit - 4, 40))
    head, partner = sim.calculate("carers_allowance", START_YEAR).astype(float)
    assert head == pytest.approx(max(rate - 40, 0) * 52, abs=0.05)
    assert partner == 0


# A supplied pre-overlap award carries no dates, so it meets the whole year's
# overlapping benefits, whatever the earnings condition says.


@pytest.mark.parametrize(
    "region, supplied, pension, expected",
    [
        ("NORTHERN_IRELAND", 4_495.40, 6_000, 0),
        ("NORTH_WEST", 4_495.40, 2_000, 2_495.40),
    ],
)
def test_a_supplied_pre_overlap_award_meets_the_whole_years_overlapping_benefits(
    region, supplied, pension, expected
):
    situation = carer(250, START_YEAR, region)
    person = situation["people"]["carer"]
    person["age"] = {START_YEAR: 70}
    person["carers_allowance_pre_overlap"] = {START_YEAR: supplied}
    person["state_pension"] = {START_YEAR: pension}
    paid = Simulation(situation=situation).calculate("carers_allowance", START_YEAR)
    assert float(paid[0]) == pytest.approx(expected, abs=0.05)


couple_cases = st.lists(
    st.tuples(
        weekly,
        weekly,
        st.floats(min_value=0, max_value=150),
        st.floats(min_value=0, max_value=150),
    ),
    min_size=CASES,
    max_size=CASES,
)


def couples_situation():
    people, benunits, households = {}, {}, {}
    for i in range(CASES):
        members = [f"head_{i}", f"partner_{i}"]
        people[members[0]] = {"age": {START_YEAR: 71}, "care_hours": {START_YEAR: 40}}
        people[members[1]] = {"age": {START_YEAR: 70}, "care_hours": {START_YEAR: 40}}
        benunits[f"benunit_{i}"] = {
            "members": members,
            "would_claim_uc": {START_YEAR: False},
        }
        households[f"household_{i}"] = {
            "members": members,
            "region": {START_YEAR: REGIONS[i % len(REGIONS)]},
        }
    return {"people": people, "benunits": benunits, "households": households}


@pytest.fixture(scope="module")
def couples_sim():
    return Simulation(situation=couples_situation())


@SETTINGS
@given(couple_cases)
def test_2030_31_couple_allowance_is_the_weekly_rule_on_each_part_of_the_year(
    couples_sim, drawn
):
    head_earnings, partner_earnings, head_pension, partner_pension = map(
        np.array, zip(*drawn)
    )
    earnings = np.column_stack([head_earnings, partner_earnings]).ravel()
    pension = np.column_stack([head_pension, partner_pension]).ravel()
    sim = couples_sim
    sim.set_input("carers_allowance_earnings", START_YEAR, 52 * earnings)
    sim.set_input("state_pension", START_YEAR, 52 * pension)
    sim.reset_calculations()
    assert sim.calculate("is_benunit_head", START_YEAR)[::2].all()
    assert sim.calculate(
        "partners_care_for_same_severely_disabled_person", START_YEAR
    ).all()
    paid = sim.calculate("carers_allowance", START_YEAR).astype(float).reshape(-1, 2)
    above = (
        sim.calculate("carers_allowance_weekly_earnings_above_limit", START_YEAR)
        .astype(float)
        .reshape(-1, 2)
    )
    _, rate = ca_parameters(START_YEAR)
    regions = np.array([REGIONS[i % len(REGIONS)] for i in range(CASES)])
    tapers = np.isin(regions, TAPER_REGIONS)[:, None]
    pension = pension.reshape(-1, 2)
    expected = np.zeros_like(paid)
    for share, under_taper in ((1 - START_YEAR_SHARE, False), (START_YEAR_SHARE, True)):
        if under_taper:
            weekly = np.where(
                above > 0, np.where(tapers, np.maximum(0, rate - above), 0), rate
            )
        else:
            weekly = np.where(above > 0, 0, rate)
        # The head when eligible, otherwise the partner.
        head_paid = weekly[:, 0] > 0
        selected = np.column_stack([head_paid, ~head_paid])
        expected += share * 52 * selected * np.maximum(0, weekly - pension)
    # Scotland pays Carer Support Payment instead.
    england_wales_ni = regions != "SCOTLAND"
    assert (np.abs(paid - expected)[england_wales_ni] <= 0.05).all()
