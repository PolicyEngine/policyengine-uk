"""Property tests for the State Pension uprating rule.

Invariants, for every input path:

1. The triple lock rate is at least each included element and the minimum
   rate, and equals one of them. Without the triple lock, the rate is
   earnings growth, or zero when earnings fall.
2. It never falls when an element rises.
3. Under the earnings-path guarantee, the pension level is never below the
   earnings path, and each year's rise is at least the rule's own rate
   (for one reading of the plan announced in September 2026, max(CPI,
   2.5%)), so the level
   is never below the path compounded at those rates either.
4. The guarantee's top-up is the smallest 0.1 percentage point step that
   meets the earnings path.
5. With the guarantee off, the path is the year-by-year rule.
6. The path agrees with an independent transcription of
   PolicyEngine/uk-triple-lock's ``rules.rates_matrix`` (the reference
   implementation of that reading of the September 2026 plan).
"""

import math

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk.parameters.gov.dwp.state_pension.triple_lock.create_triple_lock import (
    UpratingYear,
    round_to_published_precision,
    round_up_to_published_precision,
    rule_rate,
    triple_lock_rate,
    uprating_rates,
)

# Published figures are to 0.1 percentage points; draw from the range seen
# since 1990 and beyond (deflation to double-digit inflation).
published_rate = st.integers(min_value=-60, max_value=150).map(lambda n: n / 1000)
minimum_rate = st.sampled_from([0.0, 0.02, 0.025, 0.03])
LEVEL_TOLERANCE = 1e-9
# Generation is cheap, but a loaded CI runner can trip the speed check.
PROPERTIES = settings(
    max_examples=300, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)


def uprating_year(earnings_path_guarantee=st.booleans()):
    return st.builds(
        UpratingYear,
        earnings=published_rate,
        cpi=published_rate,
        minimum_rate=minimum_rate,
        active=st.booleans(),
        include_earnings=st.booleans(),
        include_inflation=st.booleans(),
        earnings_path_guarantee=earnings_path_guarantee,
    )


def paths(earnings_path_guarantee=st.booleans(), min_size=1, max_size=20):
    return st.lists(
        uprating_year(earnings_path_guarantee), min_size=min_size, max_size=max_size
    ).map(lambda years: {2030 + i: year for i, year in enumerate(years)})


@PROPERTIES
@given(
    earnings=published_rate,
    cpi=published_rate,
    floor=minimum_rate,
    include_earnings=st.booleans(),
    include_inflation=st.booleans(),
)
def test_triple_lock_is_the_highest_included_element(
    earnings, cpi, floor, include_earnings, include_inflation
):
    rate = triple_lock_rate(earnings, cpi, floor, include_earnings, include_inflation)
    assert rate >= floor
    if include_earnings:
        assert rate >= earnings
    if include_inflation:
        assert rate >= cpi
    included = [floor]
    if include_earnings:
        included.append(earnings)
    if include_inflation:
        included.append(cpi)
    assert rate in included


@PROPERTIES
@given(inputs=uprating_year())
def test_rule_rate_is_the_triple_lock_or_the_statutory_earnings_link(inputs):
    rate = rule_rate(inputs)
    if inputs.active:
        assert rate == triple_lock_rate(
            inputs.earnings,
            inputs.cpi,
            inputs.minimum_rate,
            inputs.include_earnings,
            inputs.include_inflation,
        )
    else:
        assert rate == max(inputs.earnings, 0.0)
        assert rate >= 0


@PROPERTIES
@given(
    earnings=published_rate,
    cpi=published_rate,
    floor=minimum_rate,
    rise=st.integers(min_value=1, max_value=50).map(lambda n: n / 1000),
)
def test_triple_lock_never_falls_when_an_element_rises(earnings, cpi, floor, rise):
    rate = triple_lock_rate(earnings, cpi, floor)
    assert triple_lock_rate(earnings + rise, cpi, floor) >= rate
    assert triple_lock_rate(earnings, cpi + rise, floor) >= rate
    assert triple_lock_rate(earnings, cpi, floor + rise) >= rate


@PROPERTIES
@given(years=paths(earnings_path_guarantee=st.just(False)))
def test_without_guarantee_the_path_is_the_yearly_rule(years):
    rates = uprating_rates(years)
    assert rates == {year: rule_rate(inputs) for year, inputs in years.items()}


@PROPERTIES
@given(years=paths())
def test_guarantee_keeps_the_pension_on_or_above_its_earnings_path(years):
    rates = uprating_rates(years)
    level = 1.0
    earnings_path = None
    rule_path = None
    for year in sorted(years):
        inputs = years[year]
        # Each year's rise is at least the rule's own rate.
        assert rates[year] >= rule_rate(inputs)
        if inputs.earnings_path_guarantee:
            if earnings_path is None:
                earnings_path = rule_path = level
            earnings_path *= 1 + inputs.earnings
            rule_path *= 1 + rule_rate(inputs)
        else:
            earnings_path = rule_path = None
        level *= 1 + rates[year]
        if earnings_path is not None:
            assert level >= earnings_path * (1 - LEVEL_TOLERANCE)
            assert level >= rule_path * (1 - LEVEL_TOLERANCE)


@PROPERTIES
@given(years=paths())
def test_guarantee_top_up_is_the_smallest_step_that_reaches_the_path(years):
    rates = uprating_rates(years)
    level = 1.0
    earnings_path = None
    for year in sorted(years):
        inputs = years[year]
        if inputs.earnings_path_guarantee:
            if earnings_path is None:
                earnings_path = level
            earnings_path *= 1 + inputs.earnings
            if rates[year] > rule_rate(inputs):
                one_step_less = level * (1 + rates[year] - 0.001)
                assert one_step_less < earnings_path * (1 + LEVEL_TOLERANCE)
        else:
            earnings_path = None
        level *= 1 + rates[year]


@PROPERTIES
@given(years=paths())
def test_rates_stay_on_the_published_grid(years):
    for rate in uprating_rates(years).values():
        assert rate * 1000 == pytest.approx(round(rate * 1000), abs=1e-6)


def reference_plan_rates(cpi, earnings, switch_index, floor=0.025, decimals=3):
    """Transcription of uk-triple-lock ``rules.rates_matrix`` for the
    ``burnham_2030`` policy, one draw, without numpy."""
    scale = 10**decimals

    def rnd(r):
        return round(r, decimals)

    def rnd_up(r):
        return math.ceil(round(r * scale, 9)) / scale

    rates, level, anchor = [], 1.0, 1.0
    for j, (c, e) in enumerate(zip(cpi, earnings)):
        if j < switch_index:
            rate = rnd(max(max(c, e), floor))
            level *= 1 + rate
            anchor = level
        else:
            anchor *= 1 + e
            floor_rate = rnd(max(max(c, floor), 0.0))
            rate = max(floor_rate, rnd_up(anchor / level - 1))
            level *= 1 + rate
        rates.append(rate)
    return rates


@PROPERTIES
@given(
    data=st.lists(st.tuples(published_rate, published_rate), min_size=1, max_size=15),
    switch_index=st.integers(min_value=0, max_value=15),
)
def test_plan_matches_the_uk_triple_lock_reference(data, switch_index):
    cpi = [c for c, _ in data]
    earnings = [e for _, e in data]
    years = {
        2020 + j: UpratingYear(
            earnings=e,
            cpi=c,
            minimum_rate=0.025,
            include_earnings=j < switch_index,
            earnings_path_guarantee=j >= switch_index,
        )
        for j, (c, e) in enumerate(data)
    }
    rates = uprating_rates(years)
    expected = reference_plan_rates(cpi, earnings, switch_index)
    assert [rates[year] for year in sorted(rates)] == pytest.approx(expected, abs=1e-12)


@PROPERTIES
@given(rate=st.floats(min_value=-0.5, max_value=0.5, allow_nan=False))
def test_rounding_to_published_precision(rate):
    rounded = round_to_published_precision(rate)
    assert abs(rounded - rate) <= 0.0005 + 1e-12
    assert round_to_published_precision(rounded) == rounded
    rounded_up = round_up_to_published_precision(rate)
    assert rate - 1e-9 <= rounded_up < rate + 0.001 + 1e-12


def test_rounding_takes_halves_away_from_zero():
    assert round_to_published_precision(0.0255) == 0.026
    # Round-half-even would give 0.024 and -0.024.
    assert round_to_published_precision(0.0245) == 0.025
    assert round_to_published_precision(-0.0245) == -0.025
    assert round_to_published_precision(-0.0095) == -0.010
    assert round_up_to_published_precision(0.025000000000000355) == 0.025
    assert round_up_to_published_precision(0.02500001) == 0.026


def test_plan_example_by_hand():
    """Two years under the plan: CPI 2%, earnings 4%, then CPI 2%, earnings 1%.

    Year 1 anchors the earnings path at 1 and moves it to 1.04; the floor
    pays 2.5%, so the top-up to 4.0% binds. Year 2: the path is
    1.04 x 1.01 = 1.0504 against a level of 1.04, a 1.0% rise, below the
    2.5% floor, so the floor pays.
    """
    plan = dict(
        minimum_rate=0.025, include_earnings=False, earnings_path_guarantee=True
    )
    rates = uprating_rates(
        {
            2030: UpratingYear(earnings=0.04, cpi=0.02, **plan),
            2031: UpratingYear(earnings=0.01, cpi=0.02, **plan),
        }
    )
    assert rates == {2030: 0.04, 2031: 0.025}


def test_overrides_are_paid_as_published_even_when_zero():
    rates = uprating_rates(
        {2030: UpratingYear(earnings=0.03, cpi=0.02, minimum_rate=0.025, outturn=0.0)}
    )
    assert rates == {2030: 0.0}


def test_an_override_under_the_guarantee_is_paid_as_is_and_the_path_carries_on():
    """An override sets the rate with no top-up, but the earnings path still
    grows that year: 1.05 against a level of 1.01, so the next year needs
    1.05 / 1.01 - 1 = 3.96%, rounded up to 4.0%."""
    plan = dict(
        minimum_rate=0.025, include_earnings=False, earnings_path_guarantee=True
    )
    rates = uprating_rates(
        {
            2030: UpratingYear(earnings=0.05, cpi=0.0, outturn=0.01, **plan),
            2031: UpratingYear(earnings=0.0, cpi=0.0, **plan),
        }
    )
    assert rates == {2030: 0.01, 2031: 0.04}
