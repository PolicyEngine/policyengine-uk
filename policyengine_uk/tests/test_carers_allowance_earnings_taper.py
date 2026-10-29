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
  the couple restriction picks a partner separately before and under the taper;
- an award that an input supplies, or that a reform neutralizes, calculates
  with a formula of its own or masks with defined_for, before the couple
  limit or the overlap rule is what reaches the payment, with the whole
  year's treatment, even where it equals the model's; so 2030-31 pays such
  an award as 2031-32 does, while a reform that changes only a label keeps
  the parts of the year; a mask that takes away a fraction of a penny counts,
  since the couple restriction picks whoever has an award;
- the payment reads the award before the couple limit only where the model
  calculates the award before overlap, so a supplied pre-overlap award needs
  nothing before it;
- an overlapping benefit equal to the award leaves nothing paid or received,
  a penny left over is paid, and anything paid is at least half a penny.
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
    # Anything paid is at least half a penny.
    assert ((paid == 0) | (paid >= 0.005)).all()


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


# The award passes through carers_allowance_pre_couple_limit and
# carers_allowance_pre_overlap to the payment, so a value supplied for either,
# or a reform that replaces either, reaches the amount paid.


def one_carer_couple(year):
    return {
        "people": {
            "head": {"age": {year: 71}, "care_hours": {year: 40}},
            "partner": {
                "age": {year: 70},
                "care_hours": {year: 0},
                "would_claim_carers_allowance": {year: False},
            },
        },
        "benunits": {
            "benunit": {
                "members": ["head", "partner"],
                "would_claim_uc": {year: False},
            }
        },
        "households": {
            "household": {
                "members": ["head", "partner"],
                "country": {year: "ENGLAND"},
            }
        },
    }


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
@pytest.mark.parametrize("supplied", [[0, 0], [1_000, 0]])
def test_a_supplied_award_before_the_couple_limit_is_the_award_paid(year, supplied):
    sim = Simulation(situation=one_carer_couple(year))
    sim.set_input("carers_allowance_pre_couple_limit", year, supplied)
    sim.reset_calculations()
    for name in ("carers_allowance_pre_overlap", "carers_allowance"):
        assert sim.calculate(name, year).astype(float) == pytest.approx(supplied)


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
@pytest.mark.parametrize(
    "neutralized", ["carers_allowance_pre_couple_limit", "carers_allowance_pre_overlap"]
)
def test_a_neutralized_award_is_not_paid(year, neutralized):
    from policyengine_core.reforms import Reform

    class Neutralize(Reform):
        def apply(self):
            self.neutralize_variable(neutralized)

    sim = Simulation(situation=one_carer_couple(year), reform=Neutralize)
    assert (sim.calculate("carers_allowance", year) == 0).all()
    assert not sim.calculate("receives_carers_allowance", year).any()


def both_caring_couple(year, weekly_state_pension=0, head_weekly_excess=0):
    def member(age, weekly_excess=0):
        return {
            "age": {year: age},
            "care_hours": {year: 40},
            "state_pension": {year: 52 * weekly_state_pension},
            "carers_allowance_weekly_earnings_above_limit": {year: weekly_excess},
        }

    situation = one_carer_couple(year)
    situation["people"] = {
        "head": member(71, head_weekly_excess),
        "partner": member(70),
    }
    return situation


def replaced(name, values):
    """A reform giving a variable's formula fixed values for the two people."""
    from policyengine_core.reforms import Reform

    base = Simulation(situation=both_caring_couple(START_YEAR)).tax_benefit_system
    variable = type(base.variables[name])

    class Replaced(variable):
        def formula(person, period, parameters):
            return np.array(values, dtype=float)

    Replaced.__name__ = name

    class Replace(Reform):
        def apply(self):
            self.update_variable(Replaced)

    return Replace


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
def test_a_reform_replacing_the_award_before_the_couple_limit_is_paid(year):
    # Both partners are eligible, so the parts of the year would pick the
    # head; the reform gives the award to the partner instead.
    reform = replaced("carers_allowance_pre_couple_limit", [0, 1_000])
    sim = Simulation(situation=both_caring_couple(year), reform=reform)
    for name in ("carers_allowance_pre_overlap", "carers_allowance"):
        assert sim.calculate(name, year).astype(float) == pytest.approx([0, 1_000])


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
def test_a_reform_replacing_the_award_before_overlap_meets_the_whole_years_pension(
    year,
):
    # The head is £46 a week over the earnings limit, so in 2030-31 the parts
    # of the year would pay them only under the taper. The replaced £1,000
    # carries no dates, so £400 a year of State Pension comes off it in full.
    reform = replaced("carers_allowance_pre_overlap", [1_000, 0])
    situation = both_caring_couple(year, 400 / 52, head_weekly_excess=46)
    sim = Simulation(situation=situation, reform=reform)
    paid = sim.calculate("carers_allowance", year).astype(float)
    assert paid == pytest.approx([600, 0], abs=0.01)


def reformed(name, change):
    """A reform whose formula for a variable changes the model's amounts."""
    from policyengine_core.reforms import Reform

    base = Simulation(situation=both_caring_couple(START_YEAR)).tax_benefit_system
    variable = type(base.variables[name])
    model = variable.formula

    class Reformed(variable):
        def formula(person, period, parameters):
            return change(model(person, period, parameters))

    Reformed.__name__ = name

    class Reform_(Reform):
        def apply(self):
            self.update_variable(Reformed)

    return Reform_


def updated(names, attributes):
    """A reform that updates variables' attributes, keeping their formulas
    unless the attributes give one."""
    from policyengine_core.reforms import Reform

    base = Simulation(situation=both_caring_couple(START_YEAR)).tax_benefit_system
    classes = [type(name, (type(base.variables[name]),), attributes) for name in names]

    class Update(Reform):
        def apply(self):
            for variable in classes:
                self.update_variable(variable)

    return Update


def couple_with_pension(year):
    # The head is £46 a week over the earnings limit and the partner within
    # it, each with £400 a year of State Pension.
    return both_caring_couple(year, 400 / 52, head_weekly_excess=46)


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
@pytest.mark.parametrize(
    "change",
    [
        lambda award: award * np.array([1, 0]),
        lambda award: award * np.array([1, 1.0001]),
        lambda award: award + np.array([0, 0.01]),
    ],
    ids=["partner_nil", "partner_scaled", "partner_penny"],
)
def test_a_reform_changing_only_the_partners_award_meets_the_whole_years_pension(
    year, change
):
    # A reform's formula for the award before the couple limit carries no
    # dates, even where it leaves the head's amount as the model's: the
    # restriction keeps the head's award for the whole year, and the whole
    # year's State Pension comes off it.
    model = Simulation(situation=couple_with_pension(year))
    head = float(model.calculate("carers_allowance_pre_couple_limit", year)[0])
    reform = reformed("carers_allowance_pre_couple_limit", change)
    sim = Simulation(situation=couple_with_pension(year), reform=reform)
    pre_overlap = sim.calculate("carers_allowance_pre_overlap", year).astype(float)
    assert pre_overlap == pytest.approx([head, 0])
    paid = sim.calculate("carers_allowance", year).astype(float)
    assert paid == pytest.approx([head - 400, 0], abs=0.01)


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
def test_a_reform_setting_the_models_own_award_before_overlap_meets_the_whole_years_pension(
    year,
):
    # A value can't show where it came from: an award a reform sets carries
    # no dates even where it equals the model's.
    model = Simulation(situation=couple_with_pension(year))
    award = model.calculate("carers_allowance_pre_overlap", year).astype(float)
    reform = replaced("carers_allowance_pre_overlap", award)
    sim = Simulation(situation=couple_with_pension(year), reform=reform)
    paid = sim.calculate("carers_allowance", year).astype(float)
    assert paid == pytest.approx(np.maximum(award - 400, 0), abs=0.01)


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
def test_a_reform_keeping_the_models_formulas_keeps_the_parts_of_the_year(year):
    model = Simulation(situation=couple_with_pension(year))
    expected = model.calculate("carers_allowance", year).astype(float)
    reform = updated(
        ["carers_allowance_pre_couple_limit", "carers_allowance_pre_overlap"],
        {"label": "relabelled"},
    )
    sim = Simulation(situation=couple_with_pension(year), reform=reform)
    assert sim.calculate("carers_allowance", year).astype(float) == pytest.approx(
        expected
    )
    if year == START_YEAR:
        # The head is paid only under the taper, so less than the whole
        # year's pension comes off.
        award = float(model.calculate("carers_allowance_pre_overlap", year)[0])
        assert expected[0] > award - 400 + 100


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
def test_a_reform_masking_the_award_before_the_couple_limit_keeps_the_partners(
    year,
):
    # The reform keeps the model's formula but limits the award to women, so
    # only the partner has one. The masked amounts aren't the ones the parts
    # of the year give, so the restriction sees them for the whole year and
    # leaves the partner's award with them.
    reform = updated(
        ["carers_allowance_pre_couple_limit"], {"defined_for": "is_female"}
    )
    situation = both_caring_couple(year, 400 / 52)
    situation["people"]["head"]["is_female"] = {year: False}
    situation["people"]["partner"]["is_female"] = {year: True}
    sim = Simulation(situation=situation, reform=reform)
    award = sim.calculate("carers_allowance_pre_couple_limit", year).astype(float)
    assert award[0] == 0 and award[1] > 4_000
    pre_overlap = sim.calculate("carers_allowance_pre_overlap", year).astype(float)
    assert pre_overlap == pytest.approx(award)
    paid = sim.calculate("carers_allowance", year).astype(float)
    assert paid == pytest.approx([0, award[1] - 400], abs=0.01)


def tiny_award_couple(year):
    # The head earns a hundredth of a penny a week short of tapering away the
    # whole rate, so under the taper they keep £0.0001 a week, a fraction of
    # a penny for the year; the partner is within the limit. Each has £400 a
    # year of State Pension.
    rate = ca_parameters(year)[1]
    return both_caring_couple(year, 400 / 52, head_weekly_excess=rate - 0.0001)


def test_a_fraction_of_a_penny_is_an_award_for_the_parts_of_the_year():
    # With no reform, the head's award picks the head for the weeks under the
    # taper, and the partner keeps their award for the weeks before it.
    sim = Simulation(situation=tiny_award_couple(START_YEAR))
    candidate = sim.calculate("carers_allowance_pre_couple_limit", START_YEAR)
    candidate = candidate.astype(float)
    assert 0 < candidate[0] < 0.01 and candidate[1] > 4_000
    before_taper = 1 - START_YEAR_SHARE
    pre_overlap = sim.calculate("carers_allowance_pre_overlap", START_YEAR)
    assert pre_overlap.astype(float) == pytest.approx(
        [candidate[0], candidate[1] * before_taper]
    )
    paid = sim.calculate("carers_allowance", START_YEAR).astype(float)
    assert paid == pytest.approx([0, pre_overlap[1] - before_taper * 400], abs=0.01)


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
@pytest.mark.parametrize(
    "masked", ["carers_allowance_pre_couple_limit", "carers_allowance_pre_overlap"]
)
def test_a_reform_masking_a_fraction_of_a_penny_gets_the_whole_year(year, masked):
    # The reform limits a stage to women, so it takes away the male head's
    # fraction of a penny. That is within half a penny of the parts of the
    # year, but the couple restriction picks whoever has an award, so the
    # masked stage carries no dates and the stages after it work on the whole
    # year: the partner keeps any award they have before overlap, less the
    # whole year's £400 of State Pension.
    reform = updated([masked], {"defined_for": "is_female"})
    situation = tiny_award_couple(year)
    situation["people"]["head"]["is_female"] = {year: False}
    situation["people"]["partner"]["is_female"] = {year: True}
    sim = Simulation(situation=situation, reform=reform)
    award = sim.calculate("carers_allowance_pre_couple_limit", year).astype(float)
    pre_overlap = sim.calculate("carers_allowance_pre_overlap", year).astype(float)
    if masked == "carers_allowance_pre_couple_limit":
        assert award[0] == 0 and award[1] > 4_000
        assert pre_overlap == pytest.approx(award)
    assert pre_overlap[0] == 0
    if year == START_YEAR:
        assert pre_overlap[1] > 2_000
    paid = sim.calculate("carers_allowance", year).astype(float)
    assert paid == pytest.approx(np.maximum(pre_overlap - 400, 0), abs=0.01)


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
def test_a_supplied_pre_overlap_award_needs_no_award_before_the_couple_limit(year):
    # This reform derives the award before the couple limit from the payment,
    # which works only because the supplied pre-overlap award breaks the
    # loop. A supplied pre-overlap award carries no dates, so the payment
    # doesn't read the stage before it.
    situation = carer(0, year, "NORTH_WEST")
    situation["people"]["carer"].update(
        age={year: 70},
        state_pension={year: 400},
        carers_allowance_pre_overlap={year: 1_000},
    )
    reform = updated(
        ["carers_allowance_pre_couple_limit"],
        {
            "formula": lambda person, period, parameters: (
                person("carers_allowance", period)
                + person("carers_allowance_overlapping_benefits", period)
            )
        },
    )
    paid = Simulation(situation=situation, reform=reform).calculate(
        "carers_allowance", year
    )
    assert float(paid[0]) == pytest.approx(600)


# An award a reform sets before the couple limit carries no dates, so 2030-31
# restricts it and takes overlapping benefits off it as 2031-32 does, picking
# the head where the head has an award and the partner otherwise.

reform_award = st.one_of(
    st.just(0.0), st.floats(min_value=0.01, max_value=6_000).map(lambda x: round(x, 2))
)
reform_award_cases = st.lists(
    st.tuples(
        reform_award,
        reform_award,
        st.floats(min_value=0, max_value=150),
        st.floats(min_value=0, max_value=150),
    ),
    min_size=CASES,
    max_size=CASES,
)


def reform_award_situation():
    people, benunits, households = {}, {}, {}
    years = (START_YEAR, FULL_YEAR)
    for i in range(CASES):
        members = [f"head_{i}", f"partner_{i}"]
        for name, age in zip(members, (71, 70)):
            people[name] = {
                "age": {year: age + year - START_YEAR for year in years},
                "care_hours": {year: 40 for year in years},
            }
        benunits[f"benunit_{i}"] = {
            "members": members,
            "would_claim_uc": {year: False for year in years},
        }
        households[f"household_{i}"] = {
            "members": members,
            "country": {year: "ENGLAND" for year in years},
        }
    return {"people": people, "benunits": benunits, "households": households}


@pytest.fixture(scope="module")
def reform_award_sim():
    from policyengine_core.reforms import Reform
    from policyengine_uk.model_api import YEAR, Person, Variable

    class award_set_by_reform(Variable):
        value_type = float
        entity = Person
        label = "Carer's Allowance before the couple limit, as a reform sets it"
        definition_period = YEAR

    base = Simulation(situation=both_caring_couple(START_YEAR)).tax_benefit_system
    variable = type(base.variables["carers_allowance_pre_couple_limit"])

    class carers_allowance_pre_couple_limit(variable):
        def formula(person, period, parameters):
            return person("award_set_by_reform", period)

    class SetAward(Reform):
        def apply(self):
            self.add_variable(award_set_by_reform)
            self.update_variable(carers_allowance_pre_couple_limit)

    return Simulation(situation=reform_award_situation(), reform=SetAward)


@SETTINGS
@given(reform_award_cases)
def test_2030_31_pays_an_award_a_reform_sets_as_2031_32_does(reform_award_sim, drawn):
    head_award, partner_award, head_pension, partner_pension = map(
        np.array, zip(*drawn)
    )
    award = np.column_stack([head_award, partner_award]).ravel()
    pension = np.column_stack([head_pension, partner_pension]).ravel()
    sim = reform_award_sim
    for year in (START_YEAR, FULL_YEAR):
        sim.set_input("award_set_by_reform", year, award)
        sim.set_input("state_pension", year, 52 * pension)
    sim.reset_calculations()
    paid = {
        year: sim.calculate("carers_allowance", year).astype(float).reshape(-1, 2)
        for year in (START_YEAR, FULL_YEAR)
    }
    assert paid[START_YEAR] == pytest.approx(paid[FULL_YEAR], abs=0.01)
    for year in (START_YEAR, FULL_YEAR):
        assert sim.calculate(
            "partners_care_for_same_severely_disabled_person", year
        ).all()
    award = award.reshape(-1, 2)
    head = award[:, 0] > 0
    kept = np.column_stack([head, ~head]) * award
    expected = np.maximum(0, kept - 52 * pension.reshape(-1, 2))
    expected = np.where(expected < 0.005, 0, expected)
    assert paid[START_YEAR] == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
@pytest.mark.parametrize("award", [1_000.01, 5_000.01])
def test_a_penny_left_after_overlap_is_paid(year, award):
    # Float32 stores 5,000.01 as 5,000.0098, so the penny left over is 0.98p.
    situation = carer(0, year, "NORTH_WEST")
    person = situation["people"]["carer"]
    person["age"] = {year: 70}
    person["carers_allowance_pre_overlap"] = {year: award}
    person["state_pension"] = {year: round(award - 0.01, 2)}
    sim = Simulation(situation=situation)
    assert float(sim.calculate("carers_allowance", year)[0]) == pytest.approx(
        0.01, abs=0.001
    )
    assert sim.calculate("receives_carers_allowance", year)[0]


# An overlapping benefit equal to the weekly award extinguishes it. In
# float32 the annual amounts can leave a fraction of a penny, which is not a
# payment and is not received.

residue_cases = st.lists(
    st.integers(min_value=1, max_value=9_000), min_size=CASES, max_size=CASES
)


def residue_situation(year):
    return {
        "people": {
            f"person_{i}": {"age": {year: 70}, "care_hours": {year: 40}}
            for i in range(CASES)
        },
        "benunits": {
            f"benunit_{i}": {
                "members": [f"person_{i}"],
                "would_claim_uc": {year: False},
            }
            for i in range(CASES)
        },
        "households": {
            f"household_{i}": {
                "members": [f"person_{i}"],
                "country": {year: "ENGLAND"},
            }
            for i in range(CASES)
        },
    }


@pytest.fixture(scope="module")
def residue_sims():
    return {
        year: Simulation(situation=residue_situation(year))
        for year in (START_YEAR, FULL_YEAR)
    }


@pytest.mark.parametrize("year", [START_YEAR, FULL_YEAR])
@SETTINGS
@given(drawn=residue_cases)
def test_an_overlapping_benefit_equal_to_the_award_leaves_nothing_received(
    residue_sims, year, drawn
):
    _, rate = ca_parameters(year)
    # Weekly earnings above the limit, in pence, short of the whole rate.
    excess = np.minimum(np.array(drawn), int(rate * 100) - 1) / 100
    sim = residue_sims[year]
    sim.set_input("carers_allowance_weekly_earnings_above_limit", year, excess)
    sim.set_input("state_pension", year, 52 * (rate - excess))
    sim.reset_calculations()
    assert (sim.calculate("carers_allowance", year) == 0).all()
    assert not sim.calculate("receives_carers_allowance", year).any()


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
    assert ((paid == 0) | (paid >= 0.005)).all()
