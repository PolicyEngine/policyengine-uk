"""Differential test: the triple lock computed from the statutory inputs
against every published State Pension uprating from April 2011.

The inputs are the September CPI rate and the May-July earnings growth
figure each review used (from the Explanatory Memorandum to the following
April's Up-rating Order). The rule reproduces every published rise from
April 2012 to April 2026, and every published weekly rate once rounded to
the nearest 5p. One year needs an override: in April 2011 the basic State
Pension rose by September 2010 RPI (4.6%), a one-off guarantee during the
switch from RPI to CPI, where the rule gives CPI (3.1%). The April 2022
suspension of the earnings element under the Social Security (Up-rating of
Benefits) Act 2021 is ``include_earnings`` false, not an override.

Issue #953: the rule previously used OBR calendar-year growth, which left
every uprating year 0.5-1.2pp off.
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest

from policyengine_uk.parameters.gov.dwp.state_pension.triple_lock.create_triple_lock import (
    read_uprating_years,
    rule_rate,
)
from policyengine_uk.system import system

# (April, rise, element that set it, Up-rating Order). Rates from the
# Explanatory Memorandum to each Order.
PUBLISHED_UPRATINGS = [
    (2011, 0.046, "rpi", "SI 2011/821"),
    (2012, 0.052, "cpi", "SI 2012/780"),
    (2013, 0.025, "floor", "SI 2013/574"),
    (2014, 0.027, "cpi", "SI 2014/516"),
    (2015, 0.025, "floor", "SI 2015/457"),
    (2016, 0.029, "earnings", "SI 2016/230"),
    (2017, 0.025, "floor", "SI 2017/260"),
    (2018, 0.030, "cpi", "SI 2018/281"),
    (2019, 0.026, "earnings", "SI 2019/480"),
    (2020, 0.039, "earnings", "SI 2020/234"),
    (2021, 0.025, "floor", "SI 2021/162"),
    (2022, 0.031, "cpi", "SI 2022/292"),
    (2023, 0.101, "cpi", "SI 2023/316"),
    (2024, 0.085, "earnings", "SI 2024/242"),
    (2025, 0.041, "earnings", "SI 2025/295"),
    (2026, 0.048, "earnings", "SI 2026/148"),
]

# (year, expected weekly £). Cross-referenced against gov.uk benefit and
# pension rates publications.
BASIC_STATE_PENSION_WEEKLY = [
    (2024, 169.50),
    (2025, 176.45),
    (2026, 184.90),
]

NEW_STATE_PENSION_WEEKLY = [
    (2024, 221.20),
    (2025, 230.25),
    (2026, 241.30),
]

parameters = system.parameters
state_pension = parameters.gov.dwp.state_pension
UPRATING_YEARS = read_uprating_years(parameters)


def uprating(year):
    return parameters.gov.economic_assumptions.yoy_growth.triple_lock(f"{year}-01-01")


def nearest_5p(amount):
    return float(
        (Decimal(repr(amount)) / Decimal("0.05")).quantize(Decimal(1), ROUND_HALF_UP)
        * Decimal("0.05")
    )


@pytest.mark.parametrize("year, rate, element, order", PUBLISHED_UPRATINGS)
def test_uprating_matches_published_rate(year, rate, element, order):
    assert uprating(year) == pytest.approx(rate, abs=1e-9), order


@pytest.mark.parametrize(
    "year, rate, element, order",
    [row for row in PUBLISHED_UPRATINGS if row[2] != "rpi"],
)
def test_rule_reproduces_the_rate_from_the_statutory_inputs(year, rate, element, order):
    """No override: the rule alone gives the published rate, set by the
    published element."""
    inputs = UPRATING_YEARS[year]
    assert inputs.outturn is None
    assert rule_rate(inputs) == pytest.approx(rate, abs=1e-9)
    value_by_element = {
        "earnings": inputs.earnings if inputs.include_earnings else None,
        "cpi": inputs.cpi if inputs.include_inflation else None,
        "floor": inputs.minimum_rate,
    }
    assert value_by_element[element] == pytest.approx(rate, abs=1e-9)


def test_only_april_2011_needs_an_override():
    overridden = [year for year, inputs in UPRATING_YEARS.items() if inputs.outturn]
    assert overridden == [2011]
    april_2011 = UPRATING_YEARS[2011]
    # The rule would pay September 2010 CPI; the basic State Pension rose by RPI.
    assert rule_rate(april_2011) == pytest.approx(0.031)
    assert april_2011.outturn == pytest.approx(0.046)


@pytest.mark.parametrize(
    "amount, first_year",
    [
        (state_pension.basic_state_pension.amount, 2011),
        # The new State Pension started in April 2016; the triple lock has
        # applied to it since April 2017.
        (state_pension.new_state_pension.amount, 2017),
    ],
    ids=["basic", "new"],
)
def test_published_weekly_rates_are_the_uprated_rate_to_the_nearest_5p(
    amount, first_year
):
    for year in range(first_year, 2027):
        previous = amount(f"{year - 1}-06-01")
        published = amount(f"{year}-06-01")
        assert nearest_5p(previous * (1 + uprating(year))) == pytest.approx(
            published, abs=1e-9
        ), year


def test_triple_lock_is_never_below_the_statutory_minimum():
    """Social Security Administration Act 1992 s150A requires a rise of at
    least earnings growth when earnings rise. For April 2022 the Social
    Security (Up-rating of Benefits) Act 2021 required at least the higher of
    CPI and 2.5% instead."""
    for year, inputs in UPRATING_YEARS.items():
        if year == 2022:
            statutory_minimum = max(inputs.cpi, 0.025)
        else:
            statutory_minimum = max(inputs.earnings, 0.0)
        assert uprating(year) >= statutory_minimum - 1e-12, year


@pytest.mark.parametrize("year, expected", BASIC_STATE_PENSION_WEEKLY)
def test_basic_state_pension_matches_published_rate(year, expected):
    weekly = state_pension.basic_state_pension.amount(f"{year}-04-01")
    assert weekly == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize("year, expected", NEW_STATE_PENSION_WEEKLY)
def test_new_state_pension_matches_published_rate(year, expected):
    weekly = state_pension.new_state_pension.amount(f"{year}-04-01")
    assert weekly == pytest.approx(expected, abs=0.01)
