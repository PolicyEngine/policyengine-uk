"""Every reform route writes dated changes onto the statutory timeline.

``Simulation(reform=dict)``, ``Scenario.from_reform`` (a dict or a
``Reform.from_dict`` class) and ``Scenario(parameter_changes=...)`` write
their changes onto the parameters as loaded from YAML, which are then
processed as current law is (``policyengine_uk.utils.dated_reforms``).

Invariants:

1. Statutory timeline: a change over ``[start, stop]`` holds on those dates;
   outside them the parameter follows prior law. When nothing is stated
   later, that is current law's projected path for an uprated parameter, and
   indexation from the year before for the personal allowance and the
   thresholds indexed with it (ITA 2007 ss21 and 57; cos d1344).
2. Annualisation: the annual value formulas read (1 January of fiscal year
   Y) equals an independent oracle applied to that timeline: the 30 April
   value, or the day-weighted average over 6 April to 5 April for
   ``fiscal_year_blend`` parameters.
3. Route equivalence (differential): ``"start.stop"`` keys give identical
   parameters and results through the reform dict, ``parameter_changes``,
   ``Reform.from_dict`` and either Scenario timing.
4. Documented differences between readings are kept: a bare-year dict key
   is that fiscal year only, ``Reform.from_dict`` reads it as onwards, and a
   single-day dict key overrides the annualised parameter on that day.
5. Baseline isolation: a reform never changes the simulation's baseline,
   ``parameters.baseline`` (#2188), a simulation built later, or the module
   caches, whatever the query order, and a fresh process agrees.
6. Derived parameters follow reformed values: the aligned NICs thresholds
   follow the personal allowance and a September CPI change moves the
   indexed thresholds by ITA 2007 ss21 and 57.
7. Timing: reforms applied after the data load reach the Universal Credit
   rebalancing inputs (#2252) and parameter-gated structural reforms.
"""

import datetime
import functools
import json
import subprocess
import sys
import warnings
from decimal import ROUND_CEILING, Decimal

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, example, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import Parameter, ParameterNode
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk import tax_benefit_system as tbs_module
from policyengine_uk.utils.dated_reforms import ReformPeriodWarning
from policyengine_uk.utils.scenario import Scenario

BASIC_RATE = "gov.hmrc.income_tax.rates.uk[0].rate"
PERSONAL_ALLOWANCE = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
BASIC_RATE_LIMIT = "gov.hmrc.income_tax.rates.uk[1].threshold"
UC_SINGLE_OLD = "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD"
CGT_BASIC_RATE = "gov.hmrc.cgt.basic_rate"
VAT_STANDARD_RATE = "gov.hmrc.vat.standard_rate"
PROTECTED_LCWRA = "gov.dwp.universal_credit.rebalancing.protected_health_element"
CPI_SEPTEMBER = "gov.economic_assumptions.statutory_uprating_inputs.cpi_september"
OBR_CPI = "gov.economic_assumptions.yoy_growth.obr.consumer_price_index"
NICS = "gov.hmrc.national_insurance"
PRIMARY_THRESHOLD = f"{NICS}.class_1.thresholds.primary_threshold"
SECONDARY_THRESHOLD = f"{NICS}.class_1.thresholds.secondary_threshold"
UPPER_EARNINGS_LIMIT = f"{NICS}.class_1.thresholds.upper_earnings_limit"
LOWER_PROFITS_LIMIT = f"{NICS}.class_4.thresholds.lower_profits_limit"
UPPER_PROFITS_LIMIT = f"{NICS}.class_4.thresholds.upper_profits_limit"
YEARS = range(2024, 2039)
FAR = "2100-12-31"

PROPERTY_SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)


def adult(income=30_000, years=range(2025, 2036), **extra):
    person = {"age": {2025: 40}, "employment_income": {y: income for y in years}}
    person.update(extra)
    return {
        "people": {"adult": person},
        "benunits": {"benunit": {"members": ["adult"]}},
        "households": {"household": {"members": ["adult"]}},
    }


SITUATION = adult()


def annual(simulation, path, year):
    parameter = simulation.tax_benefit_system.parameters.get_child(path)
    return float(parameter(f"{year}-01-01"))


def calculate(simulation, variable, year):
    return float(np.sum(simulation.calculate(variable, year)))


def as_dict(path, start, stop, value):
    return {path: {f"{start}.{stop}": value}}


# The routes that read a "start.stop" key the same way.
def via_reform_dict(change, situation=SITUATION):
    return Simulation(situation=situation, reform=change)


def via_parameter_changes(change, situation=SITUATION):
    return Simulation(situation=situation, scenario=Scenario(parameter_changes=change))


def via_reform_from_dict(change, situation=SITUATION):
    return Simulation(situation=situation, reform=Reform.from_dict(change))


def via_scenario_before_data_load(change, situation=SITUATION):
    scenario = Scenario.from_reform(change)
    scenario.applied_before_data_load = True
    return Simulation(situation=situation, scenario=scenario)


ROUTES = {
    "reform_dict": via_reform_dict,
    "parameter_changes": via_parameter_changes,
    "reform_from_dict": via_reform_from_dict,
    "scenario_before_data_load": via_scenario_before_data_load,
}


# An annualisation oracle written independently of
# policyengine_uk.utils.parameters.


def _day(text):
    return datetime.date.fromisoformat(text)


def timeline_value(entries, day):
    """Value of a list of (date, value) entries at a day (None before)."""
    found = None
    found_at = None
    for start, value in entries:
        if start <= day and (found_at is None or start > found_at):
            found, found_at = value, start
    return found


def oracle_annual(entries, year, blend):
    if not blend:
        return timeline_value(entries, datetime.date(year, 4, 30))
    day = datetime.date(year, 4, 6)
    end = datetime.date(year + 1, 4, 6)
    total = 0.0
    while day < end:
        total += timeline_value(entries, day)
        day += datetime.timedelta(days=1)
    return total / (end - datetime.date(year, 4, 6)).days


def projected_entries(path):
    """Current law's projected timeline of a parameter as (date, value)."""
    return [
        (_day(entry.instant_str), entry.value)
        for entry in tbs_module.projected_timelines()[path]
    ]


def overlay(entries, start, stop, value):
    """A change over [start, stop] on top of prior law's timeline."""
    after = stop + datetime.timedelta(days=1)
    prior_after = timeline_value(entries, after)
    kept = [(s, v) for s, v in entries if s < start or s > after]
    return kept + [(start, value), (after, prior_after)]


# The personal allowance is indexed from the previous tax year's allowance
# (ITA 2007 s57(3)), and Finance Act 2021 s5, as amended by Finance Act 2026
# s10, fixes it for 2022-23 to 2030-31. Prior law around a change is that
# statute (cos d1344): years a change covers take its value, years the files
# state take current law, and every other year is the year before indexed.
LAST_FROZEN_TAX_YEAR = 2030
CPI_RISE = "gov.economic_assumptions.yoy_growth.september_cpi_uprating"


def s57_step(previous, increase):
    """ITA 2007 s57(3): add the increase, rounded up to a multiple of £10."""
    if increase <= 0:
        return previous
    previous = Decimal(repr(float(previous)))
    rise = (previous * Decimal(repr(float(increase))) / 10).to_integral_value(
        ROUND_CEILING
    ) * 10
    return float(previous + rise)


def s21_step(previous, increase):
    """ITA 2007 s21(3): scale, rounded up to a multiple of £100."""
    if increase <= 0:
        return previous
    scaled = Decimal(repr(float(previous))) * (1 + Decimal(repr(float(increase))))
    return float((scaled / 100).to_integral_value(ROUND_CEILING) * 100)


def current_law_annual(path, year):
    parameter = tbs_module.processed_parameters().get_child(path)
    return float(parameter(f"{year}-01-01"))


def indexed_step(path, previous, year):
    """A threshold in an unstated ``year``, from its value the year before."""
    increase = current_law_annual(CPI_RISE, year)
    if path == PERSONAL_ALLOWANCE:
        return s57_step(previous, increase)
    if path == BASIC_RATE_LIMIT:
        return s21_step(previous, increase)
    if path == SECONDARY_THRESHOLD:
        # The model's convention: September CPI, unrounded, never cut.
        return previous * (1 + increase) if increase > 0 else previous
    # The primary threshold is aligned with the allowance.
    return round(current_law_annual(PERSONAL_ALLOWANCE, year) / 52, 2)


INDEXED_ORACLE_PATHS = (
    PERSONAL_ALLOWANCE,
    BASIC_RATE_LIMIT,
    SECONDARY_THRESHOLD,
    PRIMARY_THRESHOLD,
)


def prior_law_threshold(path, schedule, year):
    """An indexed threshold under ``schedule`` [(start, stop, value)]."""
    sample = datetime.date(year, 4, 30)
    for start, stop, value in reversed(schedule):
        if start <= sample <= stop:
            return float(value)
    if year <= LAST_FROZEN_TAX_YEAR:
        return current_law_annual(path, year)
    return indexed_step(path, prior_law_threshold(path, schedule, year - 1), year)


def statutory_allowance(schedule, year):
    """The personal allowance under ``schedule``."""
    return prior_law_threshold(PERSONAL_ALLOWANCE, schedule, year)


def expected_annual_values(path, blend, schedule):
    """Each year's annual value under ``schedule``, by prior law's rule."""
    if path in INDEXED_ORACLE_PATHS:
        return {year: prior_law_threshold(path, schedule, year) for year in YEARS}
    expected = projected_entries(path)
    for start, stop, value in schedule:
        expected = overlay(expected, start, stop, value)
    return {year: oracle_annual(expected, year, blend) for year in YEARS}


# Invariants 1-3 on the Budget cases.


@pytest.fixture(scope="module")
def baseline():
    return Simulation(situation=SITUATION)


@pytest.mark.parametrize("route", ROUTES)
def test_a_rate_change_from_6_april_sets_that_fiscal_year(route, baseline):
    simulation = ROUTES[route](as_dict(BASIC_RATE, "2027-04-06", FAR, 0.21))
    assert annual(simulation, BASIC_RATE, 2026) == 0.20
    assert annual(simulation, BASIC_RATE, 2027) == 0.21
    assert annual(simulation, BASIC_RATE, 2028) == 0.21
    # (30,000 - 12,570) x 1%: the allowance is frozen at £12,570 to 2030-31.
    for year, change in ((2026, 0), (2027, 174.30), (2028, 174.30)):
        assert calculate(simulation, "income_tax", year) - calculate(
            baseline, "income_tax", year
        ) == pytest.approx(change, abs=0.005)


@pytest.mark.parametrize("route", ROUTES)
def test_a_finite_change_ends_with_its_fiscal_year(route, baseline):
    simulation = ROUTES[route](as_dict(BASIC_RATE, "2027-04-06", "2028-04-05", 0.21))
    assert [annual(simulation, BASIC_RATE, y) for y in (2026, 2027, 2028)] == [
        0.20,
        0.21,
        0.20,
    ]
    for year, change in ((2027, 174.30), (2028, 0)):
        assert calculate(simulation, "income_tax", year) - calculate(
            baseline, "income_tax", year
        ) == pytest.approx(change, abs=0.005)


@pytest.mark.parametrize("route", ROUTES)
def test_a_one_year_change_to_an_uprated_benefit_resumes_its_uprated_path(
    route, baseline
):
    # Parameter.update would restore the 2026-27 amount (£424.90) as a stated
    # value for 2028-29 and uprate every later year from it.
    simulation = ROUTES[route](as_dict(UC_SINGLE_OLD, "2027-04-06", "2028-04-05", 500))
    assert annual(simulation, UC_SINGLE_OLD, 2027) == 500
    assert calculate(simulation, "uc_standard_allowance", 2027) == 6_000
    for year in (2026, 2028, 2029, 2033):
        assert annual(simulation, UC_SINGLE_OLD, year) == annual(
            baseline, UC_SINGLE_OLD, year
        ), year


@pytest.mark.parametrize("route", ROUTES)
def test_an_april_uprating_schedule(route, baseline):
    change = {
        UC_SINGLE_OLD: {
            "2027-04-06.2028-04-05": 500,
            f"2028-04-06.{FAR}": 520,
        }
    }
    simulation = ROUTES[route](change)
    expected = {2027: 6_000, 2028: 6_240, 2029: 6_240}
    for year, amount in expected.items():
        assert calculate(simulation, "uc_standard_allowance", year) == amount
    assert calculate(simulation, "uc_standard_allowance", 2026) == calculate(
        baseline, "uc_standard_allowance", 2026
    )


@pytest.mark.parametrize("route", ROUTES)
def test_a_reverse_ordered_schedule_matches_the_ordered_one(route):
    ordered = {UC_SINGLE_OLD: {"2027-04-06.2028-04-05": 500, f"2028-04-06.{FAR}": 520}}
    reverse = {UC_SINGLE_OLD: dict(reversed(list(ordered[UC_SINGLE_OLD].items())))}
    a, b = ROUTES[route](ordered), ROUTES[route](reverse)
    for year in YEARS:
        assert annual(a, UC_SINGLE_OLD, year) == annual(b, UC_SINGLE_OLD, year)


@pytest.mark.parametrize("route", ROUTES)
def test_a_mid_year_change_to_a_blended_rate_is_day_weighted(route):
    simulation = ROUTES[route](as_dict(CGT_BASIC_RATE, "2027-10-30", FAR, 0.20))
    # 207 days at 18% (6 April to 29 October 2027) and 159 at 20% (to
    # 5 April 2028); 2027-28 has 366 days.
    assert annual(simulation, CGT_BASIC_RATE, 2027) == pytest.approx(
        (0.18 * 207 + 0.20 * 159) / 366, abs=1e-12
    )
    assert annual(simulation, CGT_BASIC_RATE, 2026) == pytest.approx(0.18)
    assert annual(simulation, CGT_BASIC_RATE, 2028) == pytest.approx(0.20)


@pytest.mark.parametrize("route", ROUTES)
def test_an_extended_freeze_moves_the_aligned_nics_thresholds(route, baseline):
    change = {
        PERSONAL_ALLOWANCE: {"2031-04-06.2034-04-05": 12_570},
        BASIC_RATE_LIMIT: {"2031-04-06.2034-04-05": 37_700},
    }
    simulation = ROUTES[route](change)
    for year in (2031, 2032, 2033):
        assert annual(simulation, PERSONAL_ALLOWANCE, year) == 12_570
        assert annual(simulation, BASIC_RATE_LIMIT, year) == 37_700
        assert annual(simulation, LOWER_PROFITS_LIMIT, year) == 12_570
        assert annual(simulation, UPPER_PROFITS_LIMIT, year) == 50_270
        assert annual(simulation, PRIMARY_THRESHOLD, year) == pytest.approx(241.73)
        assert annual(simulation, UPPER_EARNINGS_LIMIT, year) == pytest.approx(966.73)
        # Income tax rises by 20% of the allowance current law would index.
        frozen_out = annual(baseline, PERSONAL_ALLOWANCE, year) - 12_570
        assert calculate(simulation, "income_tax", year) - calculate(
            baseline, "income_tax", year
        ) == pytest.approx(0.2 * frozen_out, abs=0.005)
    # After the freeze, indexation resumes from the frozen amounts (ITA 2007
    # s57(3) and s21(3) index the previous tax year's amount; cos d1344), and
    # the aligned NICs thresholds follow.
    allowance = 12_570
    limit = 37_700
    for year in (2034, 2035):
        increase = current_law_annual(CPI_RISE, year)
        allowance = s57_step(allowance, increase)
        limit = s21_step(limit, increase)
        assert annual(simulation, PERSONAL_ALLOWANCE, year) == allowance
        assert annual(simulation, BASIC_RATE_LIMIT, year) == limit
        assert annual(simulation, LOWER_PROFITS_LIMIT, year) == allowance
        assert annual(simulation, UPPER_PROFITS_LIMIT, year) == allowance + limit
        assert annual(simulation, PRIMARY_THRESHOLD, year) == pytest.approx(
            round(allowance / 52, 2)
        )
        frozen_out = annual(baseline, PERSONAL_ALLOWANCE, year) - allowance
        assert frozen_out > 0
        assert calculate(simulation, "income_tax", year) - calculate(
            baseline, "income_tax", year
        ) == pytest.approx(0.2 * frozen_out, abs=0.005)


def test_a_change_replacing_the_files_last_value_keeps_their_frozen_years():
    # The files state the allowance to 2030-31 with a value dated 2030-04-06.
    # A change from 2029-01-01 to 2030-12-31 replaces that value; 2028-29
    # stays frozen by Finance Act 2021 s5 rather than being indexed.
    simulation = via_reform_dict(
        {PERSONAL_ALLOWANCE: {"2029-01-01.2030-12-31": 13_000}}
    )
    assert annual(simulation, PERSONAL_ALLOWANCE, 2028) == 12_570
    assert annual(simulation, PERSONAL_ALLOWANCE, 2029) == 13_000
    assert annual(simulation, PERSONAL_ALLOWANCE, 2030) == 13_000
    assert annual(simulation, PERSONAL_ALLOWANCE, 2031) == s57_step(
        13_000, current_law_annual(CPI_RISE, 2031)
    )
    # The recorded year is processing's own; it does not reach the result.
    metadata = simulation.tax_benefit_system.parameters.get_child(
        PERSONAL_ALLOWANCE
    ).metadata
    assert "files_last_tax_year" not in metadata


def test_the_gap_between_two_allowance_changes_is_indexed_from_the_first():
    simulation = via_reform_dict(
        {
            PERSONAL_ALLOWANCE: {
                "2031-04-06.2032-04-05": 11_000,
                "2033-04-06.2034-04-05": 15_000,
            }
        }
    )
    assert annual(simulation, PERSONAL_ALLOWANCE, 2031) == 11_000
    assert annual(simulation, PERSONAL_ALLOWANCE, 2032) == s57_step(
        11_000, current_law_annual(CPI_RISE, 2032)
    )
    assert annual(simulation, PERSONAL_ALLOWANCE, 2033) == 15_000
    assert annual(simulation, PERSONAL_ALLOWANCE, 2034) == s57_step(
        15_000, current_law_annual(CPI_RISE, 2034)
    )


def test_a_change_covering_no_30_april_leaves_every_tax_year_alone():
    # 15 January to 31 March 2032 covers no tax year's 30 April sample, so
    # every annual value stays current law's; the indexed 2032-33 value
    # starts the day after the change instead of being shadowed by it.
    simulation = via_reform_dict(
        {PERSONAL_ALLOWANCE: {"2032-01-15.2032-03-31": 20_000}}
    )
    for year in YEARS:
        assert annual(simulation, PERSONAL_ALLOWANCE, year) == current_law_annual(
            PERSONAL_ALLOWANCE, year
        ), year


def test_a_change_to_an_aligned_nics_threshold_alone_realigns_after_it():
    # The model keeps the NICs thresholds aligned with their income tax
    # equivalents (create_threshold_indexation); after a change to one of
    # them alone ends, it is aligned again (cos d1344's convention for them).
    simulation = via_reform_dict({PRIMARY_THRESHOLD: {"2031-04-06.2034-04-05": 241.73}})
    for year in (2031, 2032, 2033):
        assert annual(simulation, PRIMARY_THRESHOLD, year) == pytest.approx(241.73)
    for year in (2034, 2035):
        assert annual(simulation, PRIMARY_THRESHOLD, year) == pytest.approx(
            round(current_law_annual(PERSONAL_ALLOWANCE, year) / 52, 2)
        ), year


def test_a_change_replacing_the_files_last_value_restores_their_years_after_it():
    # The files' last value (2030-04-06) is replaced by a change that covers
    # no 30 April, so 2030-31 is still the files' £12,570 and 2031-32 is
    # indexed from it.
    short = via_reform_dict({PERSONAL_ALLOWANCE: {"2030-04-06.2030-04-29": 20_000}})
    assert annual(short, PERSONAL_ALLOWANCE, 2030) == 12_570
    assert annual(short, PERSONAL_ALLOWANCE, 2031) == current_law_annual(
        PERSONAL_ALLOWANCE, 2031
    )
    # 2030 written before 2028: after 2028-29's change, 2029-30 is the files'
    # frozen £12,570, whichever order the keys come in.
    for keys in (
        {"2030": 10_000, "2028": 20_000},
        {"2028": 20_000, "2030": 10_000},
    ):
        simulation = via_reform_dict({PERSONAL_ALLOWANCE: keys})
        assert annual(simulation, PERSONAL_ALLOWANCE, 2028) == 20_000, keys
        assert annual(simulation, PERSONAL_ALLOWANCE, 2029) == 12_570, keys
        assert annual(simulation, PERSONAL_ALLOWANCE, 2030) == 10_000, keys
        assert annual(simulation, PERSONAL_ALLOWANCE, 2031) == s57_step(
            10_000, current_law_annual(CPI_RISE, 2031)
        ), keys


@pytest.mark.parametrize(
    "path, value",
    [
        (BASIC_RATE_LIMIT, 40_000),
        (SECONDARY_THRESHOLD, 120.0),
        (PRIMARY_THRESHOLD, 300.0),
    ],
)
@pytest.mark.parametrize(
    "stop", ["2030-04-05", "2030-04-29", "2030-04-30", "2030-05-01"]
)
def test_a_change_ending_around_the_files_last_value_resumes_by_their_rule(
    path, value, stop
):
    # The files' last value for each indexed threshold is in 2030-31 (from
    # 2030-04-06, or 2030-04-01 for the basic rate limit). A
    # change from 2029-04-06 that ends before 30 April 2030 covers 2029-30
    # only, so 2030-31 is the files' value; one that runs to 30 April or later
    # covers 2030-31 too, and 2031-32 resumes from it.
    simulation = via_reform_dict({path: {f"2029-04-06.{stop}": value}})
    covers_2030 = stop >= "2030-04-30"
    assert annual(simulation, path, 2029) == pytest.approx(value)
    if covers_2030:
        assert annual(simulation, path, 2030) == pytest.approx(value)
        assert annual(simulation, path, 2031) == pytest.approx(
            indexed_step(path, value, 2031)
        )
    else:
        for year in (2030, 2031):
            assert annual(simulation, path, year) == pytest.approx(
                current_law_annual(path, year)
            ), year


@pytest.mark.parametrize(
    "path, value",
    [
        (PERSONAL_ALLOWANCE, 15_000),
        (BASIC_RATE_LIMIT, 40_000),
        (SECONDARY_THRESHOLD, 120.0),
        (PRIMARY_THRESHOLD, 300.0),
    ],
)
def test_an_eternity_change_holds_an_indexed_threshold_flat(path, value):
    # Reform.from_dict's ETERNITY key starts the change in year 1; its tax
    # years were compared unpadded, so indexation resumed after 2030.
    simulation = via_reform_from_dict({path: {"ETERNITY": value}})
    for year in YEARS:
        assert annual(simulation, path, year) == pytest.approx(value), year
    if path == PERSONAL_ALLOWANCE:
        # The primary threshold is aligned with it after the files' years.
        for year in range(LAST_FROZEN_TAX_YEAR + 1, YEARS.stop):
            assert annual(simulation, PRIMARY_THRESHOLD, year) == round(
                value / 52, 2
            ), year


def test_bare_year_dict_keys_match_the_fiscal_year_interval():
    by_year = via_reform_dict(
        {PERSONAL_ALLOWANCE: {"2031": 12_570, "2032": 12_570, "2033": 12_570}}
    )
    by_interval = via_reform_dict(
        {PERSONAL_ALLOWANCE: {"2031-04-06.2034-04-05": 12_570}}
    )
    for path in (PERSONAL_ALLOWANCE, PRIMARY_THRESHOLD, LOWER_PROFITS_LIMIT):
        for year in YEARS:
            assert annual(by_year, path, year) == annual(by_interval, path, year)


def test_a_september_cpi_change_moves_the_indexed_thresholds_by_statute():
    simulation = via_reform_dict(
        as_dict(CPI_SEPTEMBER, "2030-09-01", "2031-08-31", 0.05)
    )
    # s57(3): 12,570 x 5% = 628.50, rounded up to 630. s21(3): 37,700 x 1.05
    # = 39,585, rounded up to 39,600.
    assert annual(simulation, PERSONAL_ALLOWANCE, 2031) == 13_200
    assert annual(simulation, BASIC_RATE_LIMIT, 2031) == 39_600
    assert annual(simulation, PRIMARY_THRESHOLD, 2031) == pytest.approx(253.85)


# Invariant 7: timing.


def test_a_dict_reform_reaches_the_uc_rebalancing_inputs():
    situation = adult(income=0, uc_limited_capability_for_WRA={2027: True})
    for route in ("reform_dict", "parameter_changes", "reform_from_dict"):
        simulation = ROUTES[route](
            as_dict(PROTECTED_LCWRA, "2027-04-06", "2028-04-05", 500.0), situation
        )
        assert calculate(simulation, "uc_LCWRA_element", 2027) == 6_000, route


def test_a_dict_reform_switches_on_a_parameter_gated_structural_reform():
    switch = "gov.contrib.cps.marriage_tax_reforms.expanded_ma.remove_income_condition"
    situation = {
        "people": {
            "earner": {"age": {2026: 40}, "employment_income": {2026: 80_000}},
            "partner": {"age": {2026: 40}},
        },
        "benunits": {
            "benunit": {"members": ["earner", "partner"], "is_married": {2026: True}}
        },
        "households": {"household": {"members": ["earner", "partner"]}},
    }
    simulation = via_reform_dict(
        as_dict(switch, "2025-01-01", "2030-12-31", True), situation
    )
    # 10% of the £12,570 allowance, rounded up to the next £10.
    assert calculate(simulation, "marriage_allowance", 2026) == 1_260


# Invariant 4: documented readings.


def test_a_bare_year_is_that_year_in_a_dict_and_onwards_in_reform_from_dict():
    change = {BASIC_RATE: {"2027": 0.21}}
    as_dict_ = via_reform_dict(change)
    as_class = via_reform_from_dict(change)
    assert [annual(as_dict_, BASIC_RATE, y) for y in (2026, 2027, 2028)] == [
        0.20,
        0.21,
        0.20,
    ]
    assert [annual(as_class, BASIC_RATE, y) for y in (2026, 2027, 2028)] == [
        0.20,
        0.21,
        0.21,
    ]


def test_a_single_day_dict_key_keeps_its_legacy_meaning_and_warns():
    # The warning is raised after the simulation loads the variable modules,
    # so this also checks that loading them leaves the filters alone (#2377).
    with pytest.warns(ReformPeriodWarning, match="2027-04-06.2100-12-31"):
        april = via_reform_dict({BASIC_RATE: {"2027-04-06": 0.21}})
    assert [annual(april, BASIC_RATE, y) for y in YEARS] == [0.20] * len(YEARS)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ReformPeriodWarning)
        january = via_reform_dict({BASIC_RATE: {"2027-01-01": 0.21}})
    assert [annual(january, BASIC_RATE, y) for y in (2026, 2027, 2028)] == [
        0.20,
        0.21,
        0.20,
    ]


def test_scalar_readings():
    as_dict_ = via_reform_dict({BASIC_RATE: 0.21})
    as_changes = via_parameter_changes({BASIC_RATE: 0.21})
    for simulation in (as_dict_, as_changes):
        assert [annual(simulation, BASIC_RATE, y) for y in (2023, 2027, 2038)] == [
            0.21
        ] * 3
    assert annual(as_dict_, BASIC_RATE, 2022) == 0.20
    assert annual(as_changes, BASIC_RATE, 2022) == 0.21


def test_a_path_the_model_does_not_define_is_rejected():
    for route in ROUTES:
        with pytest.raises(Exception, match="new_credit"):
            ROUTES[route](
                {"gov.budget_2026.new_credit.amount": {f"2027-04-06.{FAR}": 500}}
            )


def test_a_parameter_added_by_a_structural_reform_in_the_tuple_can_be_set():
    from policyengine_core.parameters import ParameterNode

    class add_bonus(Reform):
        def apply(self):
            self.parameters.add_child(
                "test_budget",
                ParameterNode(
                    "test_budget", data={"bonus": {"values": {"2000-01-01": 1}}}
                ),
            )

    simulation = Simulation(
        situation=SITUATION, reform=(add_bonus, {"test_budget.bonus": 7})
    )
    assert simulation.tax_benefit_system.parameters.test_budget.bonus("2027-01-01") == 7


# Invariant 1 and 2 by sampling: random changes against the oracle.

SAMPLED = {
    BASIC_RATE: (False, st.sampled_from([0.15, 0.19, 0.21, 0.25])),
    UC_SINGLE_OLD: (False, st.sampled_from([350.0, 480.0, 512.5, 600.0])),
    PERSONAL_ALLOWANCE: (False, st.sampled_from([11_000, 12_570, 15_000])),
    CGT_BASIC_RATE: (True, st.sampled_from([0.1, 0.2, 0.24])),
}
dates = st.dates(datetime.date(2025, 1, 1), datetime.date(2033, 12, 31))


@st.composite
def changes(draw):
    path = draw(st.sampled_from(sorted(SAMPLED)))
    blend, values = SAMPLED[path]
    start = draw(dates)
    open_ended = draw(st.booleans())
    if open_ended:
        stop = datetime.date(2100, 12, 31)
    else:
        stop = start + datetime.timedelta(days=draw(st.integers(0, 1_500)))
    return path, blend, start, stop, draw(values)


@PROPERTY_SETTINGS
@given(change=changes())
def test_reformed_annual_values_match_the_oracle(change):
    path, blend, start, stop, value = change
    simulation = via_reform_dict(as_dict(path, start, stop, value))
    expected = expected_annual_values(path, blend, [(start, stop, value)])
    expected_timeline = overlay(projected_entries(path), start, stop, value)
    projected = [
        (_day(entry.instant_str), entry.value)
        for entry in simulation.tax_benefit_system.projected_timelines[path]
    ]
    for year in YEARS:
        # Invariant 1: the statutory timeline, at the 30 April sample.
        sample = datetime.date(year, 4, 30)
        assert timeline_value(projected, sample) == pytest.approx(
            expected[year]
            if path in INDEXED_ORACLE_PATHS
            else timeline_value(expected_timeline, sample)
        ), year
        # Invariant 2: the annual value.
        assert annual(simulation, path, year) == pytest.approx(
            expected[year], abs=1e-9
        ), year


@PROPERTY_SETTINGS
@given(change=changes(), income=st.integers(0, 150_000))
def test_routes_agree_on_start_stop_keys(change, income):
    path, _, start, stop, value = change
    situation = adult(income=income)
    reform = as_dict(path, start, stop, value)
    simulations = {name: route(reform, situation) for name, route in ROUTES.items()}
    first = simulations["reform_dict"]
    for name, simulation in simulations.items():
        for year in (2026, 2028, 2031, 2034):
            assert annual(simulation, path, year) == annual(first, path, year), name
            assert calculate(simulation, "income_tax", year) == calculate(
                first, "income_tax", year
            ), name


# Invariant 5: baseline isolation.


def parameter_digest(parameters, paths, years=YEARS):
    return {
        path: [float(parameters.get_child(path)(f"{year}-01-01")) for year in years]
        for path in paths
    }


DIGEST_PATHS = [
    BASIC_RATE,
    PERSONAL_ALLOWANCE,
    UC_SINGLE_OLD,
    PRIMARY_THRESHOLD,
    CGT_BASIC_RATE,
    VAT_STANDARD_RATE,
]
OUTPUTS = ["income_tax", "national_insurance", "uc_standard_allowance"]


def outputs(simulation, order=1):
    pairs = [(variable, year) for variable in OUTPUTS for year in (2026, 2027, 2031)]
    return {
        f"{variable}:{year}": calculate(simulation, variable, year)
        for variable, year in pairs[::order]
    }


VAT_SITUATION = {
    "people": {"adult": {"age": {2026: 40}}},
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {
        "household": {
            "members": ["adult"],
            "full_rate_vat_consumption": {2026: 10_000},
            "reduced_rate_vat_consumption": {2026: 0},
        }
    },
}


@pytest.mark.parametrize(
    "route, change",
    [
        ("reform_dict", {VAT_STANDARD_RATE: 0.22}),
        ("parameter_changes", {VAT_STANDARD_RATE: 0.22}),
        ("parameter_changes", {VAT_STANDARD_RATE: {"2026": 0.22}}),
        ("reform_from_dict", as_dict(VAT_STANDARD_RATE, "2026-01-01", FAR, 0.22)),
        ("scenario_before_data_load", {VAT_STANDARD_RATE: 0.22}),
    ],
)
def test_baseline_vat_is_current_law_on_every_route(route, change):
    unreformed = Simulation(situation=VAT_SITUATION)
    simulation = ROUTES[route](change, VAT_SITUATION)
    vat = calculate(simulation, "vat", 2026)
    assert vat > calculate(unreformed, "vat", 2026)
    assert calculate(simulation, "baseline_vat", 2026) == calculate(
        unreformed, "vat", 2026
    )
    assert simulation.tax_benefit_system.parameters.baseline.gov.hmrc.vat.standard_rate(
        "2026-06-01"
    ) == pytest.approx(0.20)


def test_reforms_leave_baselines_caches_and_later_simulations_alone():
    reference = outputs(Simulation(situation=SITUATION))
    processed = parameter_digest(tbs_module.processed_parameters(), DIGEST_PATHS)
    statutory = parameter_digest(tbs_module.statutory_parameters(), DIGEST_PATHS)
    reforms = [
        as_dict(BASIC_RATE, "2027-04-06", FAR, 0.21),
        as_dict(UC_SINGLE_OLD, "2027-04-06", "2028-04-05", 500),
        {PERSONAL_ALLOWANCE: {"2031": 12_570}},
        as_dict(CPI_SEPTEMBER, "2030-09-01", "2031-08-31", 0.05),
    ]
    for reform in reforms:
        for route in ROUTES.values():
            simulation = route(reform)
            assert outputs(simulation.baseline) == reference
            assert outputs(simulation.baseline, order=-1) == reference
    assert outputs(Simulation(situation=SITUATION)) == reference
    assert outputs(Simulation(situation=SITUATION), order=-1) == reference
    assert (
        parameter_digest(tbs_module.processed_parameters(), DIGEST_PATHS) == processed
    )
    assert (
        parameter_digest(tbs_module.statutory_parameters(), DIGEST_PATHS) == statutory
    )


FRESH_PROCESS = """
import json
from policyengine_uk import Simulation
from policyengine_uk.tests.test_dated_reform_routes import SITUATION, outputs, BASIC_RATE
reform = Simulation(situation=SITUATION, reform={BASIC_RATE: {"2027-04-06.2100-12-31": 0.21}})
print(json.dumps({"baseline": outputs(Simulation(situation=SITUATION)), "reform": outputs(reform)}))
"""


def test_a_fresh_process_agrees_with_a_warm_one():
    for _ in range(2):
        warm_reform = via_reform_dict(as_dict(BASIC_RATE, "2027-04-06", FAR, 0.21))
    warm = {
        "baseline": outputs(Simulation(situation=SITUATION)),
        "reform": outputs(warm_reform),
    }
    result = subprocess.run(
        [sys.executable, "-c", FRESH_PROCESS],
        capture_output=True,
        text=True,
        check=True,
    )
    cold = json.loads(result.stdout.strip().splitlines()[-1])
    assert cold == warm


def test_rebuilding_from_the_statutory_cache_matches_loading_the_yaml():
    from policyengine_uk.tax_benefit_system import CountryTaxBenefitSystem

    fresh = CountryTaxBenefitSystem()
    fresh.reset_parameters()
    fresh.process_parameters()
    rebuilt = CountryTaxBenefitSystem()
    rebuilt.parameters = tbs_module.statutory_parameters()
    rebuilt.process_parameters()
    for parameter in fresh.parameters.gov.get_descendants():
        if not isinstance(parameter, Parameter):
            continue
        other = rebuilt.parameters.get_child(parameter.name)
        for year in (2015, 2026, 2031, 2040):
            assert other(f"{year}-01-01") == parameter(f"{year}-01-01"), parameter.name


# Reference arithmetic for the statute the indexation follows, kept here so
# the CPI case above has an oracle independent of create_threshold_indexation.
def test_statutory_arithmetic_for_the_cpi_case():
    increase = Decimal("0.05")
    step = (Decimal(12_570) * increase / 10).to_integral_value(ROUND_CEILING) * 10
    assert 12_570 + step == 13_200
    brl = (Decimal(37_700) * (1 + increase) / 100).to_integral_value(ROUND_CEILING)
    assert brl * 100 == 39_600


def test_prior_law_after_a_bounded_change_follows_the_reforms_other_changes():
    # Benefits are uprated by the OBR CPI forecast (gov.benefit_uprating_cpi
    # follows its lagged index). With a higher 2027 CPI in the same reform,
    # the uprated path the benefit resumes after its one-year change is the
    # one under that CPI, not current law's.
    cpi = as_dict(OBR_CPI, "2027-01-01", "2027-12-31", 0.08)
    benefit = as_dict(UC_SINGLE_OLD, "2027-04-06", "2028-04-05", 500)
    cpi_only = via_reform_dict(cpi)
    both = via_reform_dict({**cpi, **benefit})
    assert annual(both, UC_SINGLE_OLD, 2027) == 500
    for year in (2028, 2029, 2031):
        assert annual(both, UC_SINGLE_OLD, year) == pytest.approx(
            annual(cpi_only, UC_SINGLE_OLD, year)
        ), year
    assert annual(cpi_only, UC_SINGLE_OLD, 2028) != annual(
        Simulation(situation=SITUATION), UC_SINGLE_OLD, 2028
    )


@st.composite
def two_changes(draw):
    path = draw(st.sampled_from(sorted(SAMPLED)))
    blend, values = SAMPLED[path]
    first = draw(dates)
    gap = draw(st.integers(1, 900))
    length = draw(st.integers(0, 900))
    second = first + datetime.timedelta(days=gap)
    # Back to back, or with a gap between the changes.
    space = draw(st.integers(0, 700))
    first_stop = max(first, second - datetime.timedelta(days=1 + space))
    second_stop = second + datetime.timedelta(days=length)
    return (
        path,
        blend,
        [(first, first_stop, draw(values)), (second, second_stop, draw(values))],
    )


@PROPERTY_SETTINGS
@given(change=two_changes(), reverse=st.booleans())
def test_a_schedule_of_two_changes_matches_the_oracle(change, reverse):
    path, blend, schedule = change
    keys = [(f"{start}.{stop}", value) for start, stop, value in schedule]
    if reverse:
        keys.reverse()
    simulation = via_reform_dict({path: dict(keys)})
    expected = expected_annual_values(path, blend, schedule)
    for year in YEARS:
        assert annual(simulation, path, year) == pytest.approx(
            expected[year], abs=1e-9
        ), year


INDEXED_SAMPLED = {
    PERSONAL_ALLOWANCE: st.sampled_from([11_000, 12_570, 15_000]),
    BASIC_RATE_LIMIT: st.sampled_from([37_700, 40_000, 50_270]),
    SECONDARY_THRESHOLD: st.sampled_from([96.0, 120.0, 175.0]),
    PRIMARY_THRESHOLD: st.sampled_from([241.73, 300.0]),
}


@st.composite
def indexed_schedules(draw):
    """One to three changes to an indexed threshold, with or without gaps."""
    path = draw(st.sampled_from(sorted(INDEXED_SAMPLED)))
    start = draw(dates)
    schedule = []
    for _ in range(draw(st.integers(1, 3))):
        stop = start + datetime.timedelta(days=draw(st.integers(0, 900)))
        schedule.append((start, stop, draw(INDEXED_SAMPLED[path])))
        start = stop + datetime.timedelta(days=1 + draw(st.integers(0, 700)))
    if draw(st.booleans()):
        last_start, _, last_value = schedule[-1]
        schedule[-1] = (last_start, datetime.date(2100, 12, 31), last_value)
    return path, schedule


# The fixed examples cover what the derandomised draws miss: a change that
# replaces the files' last value and ends before 30 April 2030, bounded
# changes ending after the files' years, and three changes.
@PROPERTY_SETTINGS
@given(change=indexed_schedules(), reverse=st.booleans())
@example(
    change=(
        BASIC_RATE_LIMIT,
        [(datetime.date(2029, 4, 6), datetime.date(2030, 4, 29), 40_000)],
    ),
    reverse=False,
)
@example(
    change=(
        SECONDARY_THRESHOLD,
        [(datetime.date(2030, 4, 6), datetime.date(2030, 4, 20), 120.0)],
    ),
    reverse=False,
)
@example(
    change=(
        PERSONAL_ALLOWANCE,
        [(datetime.date(2031, 4, 6), datetime.date(2033, 4, 5), 15_000)],
    ),
    reverse=False,
)
@example(
    change=(
        SECONDARY_THRESHOLD,
        [(datetime.date(2031, 4, 6), datetime.date(2034, 4, 5), 175.0)],
    ),
    reverse=False,
)
@example(
    change=(
        PRIMARY_THRESHOLD,
        [(datetime.date(2031, 4, 6), datetime.date(2032, 4, 5), 300.0)],
    ),
    reverse=False,
)
@example(
    change=(
        PERSONAL_ALLOWANCE,
        [
            (datetime.date(2026, 4, 6), datetime.date(2027, 4, 5), 11_000),
            (datetime.date(2029, 4, 6), datetime.date(2031, 4, 5), 15_000),
            (datetime.date(2033, 4, 6), datetime.date(2100, 12, 31), 12_570),
        ],
    ),
    reverse=True,
)
def test_indexed_threshold_schedules_match_prior_law(change, reverse):
    path, schedule = change
    keys = [(f"{start}.{stop}", value) for start, stop, value in schedule]
    if reverse:
        keys.reverse()
    simulation = via_reform_dict({path: dict(keys)})
    for year in YEARS:
        assert annual(simulation, path, year) == pytest.approx(
            prior_law_threshold(path, schedule, year), abs=1e-9
        ), year


# Review round 1 (GPT-6.1 Sol): rebuilds keep every change.


@pytest.mark.parametrize("name", ["no_economic_assumptions", "reindex_benefit_cap"])
def test_a_modifier_that_reprocesses_the_parameters_keeps_the_reform(name):
    import importlib

    module = importlib.import_module(f"policyengine_uk.scenarios.{name}")
    reprocessing = getattr(module, name)
    reform = Scenario.from_reform(as_dict(BASIC_RATE, "2027-04-06", FAR, 0.21))
    for scenario in (reprocessing + reform, reform + reprocessing):
        simulation = Simulation(situation=SITUATION, scenario=scenario)
        assert annual(simulation, BASIC_RATE, 2028) == 0.21, name
        assert annual(simulation, BASIC_RATE, 2026) == 0.20, name
        assert (
            simulation.tax_benefit_system.parameters.baseline.gov.hmrc.income_tax.rates.uk.brackets[
                0
            ].rate("2028-06-01")
            == pytest.approx(0.20)
        )
    if name == "no_economic_assumptions":
        # The scenario's own effect also holds: thresholds stay frozen.
        assert annual(simulation, PERSONAL_ALLOWANCE, 2035) == 12_570


DIVIDEND_BASIC_RATE = "gov.hmrc.income_tax.rates.dividends[0].rate"


def _dividend_baseline(simulation):
    # Sets a parameter on the annualised tree, as a dashboard baseline does.
    simulation.tax_benefit_system.parameters.get_child(DIVIDEND_BASIC_RATE).update(
        period="year:2026:20", value=0.0875
    )


@pytest.mark.parametrize("before_data_load", [False, True])
def test_a_scenario_keeps_its_modifiers_parameters_and_its_parameter_changes(
    before_data_load,
):
    # In 2.125.1 the parameter changes rebuilt the parameters after the
    # modifier ran, so its 8.75% dividend rate reverted to 10.75%.
    situation = adult(dividend_income={year: 10_000 for year in range(2025, 2036)})
    both = {
        DIVIDEND_BASIC_RATE: {f"2026-01-01.{FAR}": 0.0875},
        BASIC_RATE: {f"2027-04-06.{FAR}": 0.21},
    }
    reference = via_reform_dict(both, situation)
    modifier = Scenario(simulation_modifier=_dividend_baseline)
    changes = Scenario(parameter_changes=as_dict(BASIC_RATE, "2027-04-06", FAR, 0.21))
    for scenario in (modifier + changes, changes + modifier):
        scenario.applied_before_data_load = before_data_load
        simulation = Simulation(situation=situation, scenario=scenario)
        for year in (2026, 2027, 2028):
            assert annual(simulation, DIVIDEND_BASIC_RATE, year) == 0.0875
            assert annual(simulation, BASIC_RATE, year) == annual(
                reference, BASIC_RATE, year
            )
            assert calculate(simulation, "income_tax", year) == pytest.approx(
                calculate(reference, "income_tax", year), abs=1e-6
            )
        assert annual(simulation.baseline, DIVIDEND_BASIC_RATE, 2027) == 0.1075


def test_scenario_apply_adds_to_the_changes_a_simulation_already_has():
    simulation = via_reform_dict(as_dict(BASIC_RATE, "2027-04-06", FAR, 0.21))
    Scenario.from_reform({UC_SINGLE_OLD: {"2027": 500}}).apply(simulation)
    assert annual(simulation, BASIC_RATE, 2028) == 0.21
    assert annual(simulation, UC_SINGLE_OLD, 2027) == 500
    # Scenario.apply edits the annualised parameters, as it always has; the
    # system keeps the edit so a later rebuild applies it again.
    system = simulation.tax_benefit_system
    assert len(system.dated_assignments) == 1
    assert len(system.legacy_overrides) == 1
    simulation.apply_parameter_changes({PERSONAL_ALLOWANCE: {"2027": 13_000}})
    assert annual(simulation, BASIC_RATE, 2028) == 0.21
    assert annual(simulation, UC_SINGLE_OLD, 2027) == 500
    assert annual(simulation, PERSONAL_ALLOWANCE, 2027) == 13_000


# Review round 2 (GPT-6.1 Sol): Scenario.apply never rebuilds, rebuilds keep
# a modifier's base, failures roll back, and the memo is isolated.


def test_scenario_apply_keeps_a_structural_reforms_parameter():
    from policyengine_core.parameters import ParameterNode

    class add_bonus(Reform):
        def apply(self):
            self.parameters.add_child(
                "test_budget",
                ParameterNode(
                    "test_budget", data={"bonus": {"values": {"2000-01-01": 1}}}
                ),
            )

    simulation = Simulation(
        situation=SITUATION, reform=(add_bonus, {"test_budget.bonus": 7})
    )
    Scenario.from_reform({BASIC_RATE: {"2027": 0.21}}).apply(simulation)
    parameters = simulation.tax_benefit_system.parameters
    assert parameters.test_budget.bonus("2027-01-01") == 7
    assert annual(simulation, BASIC_RATE, 2027) == 0.21


def test_later_changes_keep_a_reprocessing_modifiers_edits():
    from policyengine_uk.scenarios.no_economic_assumptions import (
        no_economic_assumptions,
    )

    simulation = Simulation(situation=SITUATION, scenario=no_economic_assumptions)
    assert annual(simulation, PERSONAL_ALLOWANCE, 2035) == 12_570
    Scenario.from_reform({BASIC_RATE: {"2027": 0.21}}).apply(simulation)
    assert annual(simulation, PERSONAL_ALLOWANCE, 2035) == 12_570
    # A rebuild starts from the parameters as the modifier left them.
    simulation.apply_parameter_changes({UC_SINGLE_OLD: {"2027": 500}})
    assert annual(simulation, PERSONAL_ALLOWANCE, 2035) == 12_570
    assert annual(simulation, BASIC_RATE, 2027) == 0.21
    assert annual(simulation, UC_SINGLE_OLD, 2027) == 500


def test_scenario_apply_and_construction_give_a_scenario_the_same_precedence():
    scenario = Scenario(parameter_changes={BASIC_RATE: 0.21}) + Scenario.from_reform(
        {BASIC_RATE: {"2027": 0.22}}
    )
    constructed = Simulation(situation=SITUATION, scenario=scenario)
    applied = Simulation(situation=SITUATION)
    scenario.apply(applied)
    for year in (2026, 2027, 2028):
        assert annual(applied, BASIC_RATE, year) == annual(
            constructed, BASIC_RATE, year
        ), year
    assert annual(constructed, BASIC_RATE, 2027) == 0.22
    assert annual(constructed, BASIC_RATE, 2028) == 0.21


def test_a_failed_change_leaves_the_system_as_it_was():
    simulation = via_reform_dict(as_dict(BASIC_RATE, "2027-04-06", FAR, 0.21))
    system = simulation.tax_benefit_system
    with pytest.raises(ValueError):
        Scenario.from_reform({"gov.not_a_real_parameter": {"2027": 1}}).apply(
            simulation
        )
    with pytest.raises(ValueError):
        simulation.apply_parameter_changes({"gov.not_a_real_parameter": {"2027": 1}})
    assert len(system.dated_assignments) == 1
    assert system.legacy_overrides == []
    assert annual(simulation, BASIC_RATE, 2028) == 0.21
    # A valid change still applies afterwards.
    simulation.apply_parameter_changes({UC_SINGLE_OLD: {"2027": 500}})
    assert annual(simulation, UC_SINGLE_OLD, 2027) == 500
    assert annual(simulation, BASIC_RATE, 2028) == 0.21


def _system_with(path, value, dates=f"2027-04-06.{FAR}"):
    from policyengine_uk.utils.dated_reforms import read_reform_dict

    system = tbs_module.system.clone()
    changes, _ = read_reform_dict({path: {dates: value}}, lambda _: True)
    system.apply_parameter_assignments(changes)
    return system


def test_the_rebuild_memo_cannot_be_changed_through_a_system():
    sources = "gov.dwp.universal_credit.means_test.capital.person_sources"
    dates = f"2016-04-06.{FAR}"
    value = ["lifetime_isa_countable_capital"]
    first = _system_with(sources, list(value), dates)
    first.parameters.get_child(sources)("2027-01-01").append("employment_income")
    later = _system_with(sources, list(value), dates)
    assert later.parameters.get_child(sources)("2027-01-01") == value
    # Values that are not plain numbers, booleans or strings are not keyed.
    assert tbs_module._assignments_key(later.dated_assignments) is None

    class Rate(float):
        def __repr__(self):
            return "0.21111"

    _system_with(BASIC_RATE, 0.21111)
    disguised = _system_with(BASIC_RATE, Rate(0.22222))
    assert float(disguised.parameters.get_child(BASIC_RATE)("2028-01-01")) == 0.22222

    # Two systems with one memoised reform share no timeline with each other
    # or with the cache.
    a, b = _system_with(BASIC_RATE, 0.23), _system_with(BASIC_RATE, 0.23)
    assert a.projected_timelines[BASIC_RATE] is not b.projected_timelines[BASIC_RATE]
    a.parameters.get_child(BASIC_RATE).update(period="2028", value=0.5)
    assert float(b.parameters.get_child(BASIC_RATE)("2028-01-01")) == 0.23
    assert (
        float(
            _system_with(BASIC_RATE, 0.23).parameters.get_child(BASIC_RATE)(
                "2028-01-01"
            )
        )
        == 0.23
    )


def test_prior_law_that_never_settles_is_an_error(monkeypatch):
    # Projections that keep changing from pass to pass mean the changes'
    # prior law depends on itself.
    from policyengine_core.parameters.parameter_at_instant import ParameterAtInstant
    from policyengine_uk.utils.dated_reforms import read_reform_dict

    calls = {"n": 0}

    def unsettled(tree, unreformed=None, annualise=True, generated=None):
        calls["n"] += 1
        entry = ParameterAtInstant(
            UC_SINGLE_OLD, "2026-04-01", data={"value": float(calls["n"])}
        )
        return tree, {UC_SINGLE_OLD: [entry]}

    changes, _ = read_reform_dict(
        as_dict(UC_SINGLE_OLD, "2027-04-06", "2028-04-05", 500), lambda _: True
    )
    monkeypatch.setattr(tbs_module, "process_parameter_tree", unsettled)
    with pytest.raises(ValueError, match="depend on each other in a cycle"):
        tbs_module.prior_law_projection(changes, tbs_module.statutory_parameters())


def test_two_changes_that_need_projection_see_each_other():
    # A one-year primary threshold change inside an allowance freeze: after
    # it, prior law is the threshold aligned with the frozen allowance.
    simulation = via_reform_dict(
        {
            PERSONAL_ALLOWANCE: {"2031-04-06.2035-04-05": 12_570},
            PRIMARY_THRESHOLD: {"2031": 250},
        }
    )
    assert annual(simulation, PRIMARY_THRESHOLD, 2031) == 250
    for year in (2032, 2033, 2034):
        assert annual(simulation, PRIMARY_THRESHOLD, year) == pytest.approx(241.73), (
            year
        )


def test_mixed_single_day_and_dated_keys_warn_and_apply_single_days_last():
    with pytest.warns(ReformPeriodWarning, match="mixes single-day keys"):
        simulation = via_reform_dict(
            {BASIC_RATE: {"2027-01-01": 0.21, "2026-01-01.2100-12-31": 0.22}}
        )
    assert annual(simulation, BASIC_RATE, 2027) == 0.21
    assert annual(simulation, BASIC_RATE, 2028) == 0.22


def test_the_projected_timelines_cache_is_a_copy_and_reforms_leave_it_alone():
    cache = tbs_module.projected_timelines()
    live = tbs_module.system.parameters
    for name in (CPI_SEPTEMBER, UC_SINGLE_OLD):
        assert cache[name] is not live.get_child(name).values_list
    before = {
        name: [(e.instant_str, e.value) for e in cache[name]]
        for name in (CPI_SEPTEMBER, UC_SINGLE_OLD, PERSONAL_ALLOWANCE)
    }
    via_reform_dict(as_dict(UC_SINGLE_OLD, "2027-04-06", "2028-04-05", 500))
    via_reform_dict({PERSONAL_ALLOWANCE: {"2031": 12_570}})
    after = {name: [(e.instant_str, e.value) for e in cache[name]] for name in before}
    assert after == before


def test_a_repeated_reform_reuses_the_rebuilt_parameters():
    reform = as_dict(BASIC_RATE, "2027-04-06", "2029-04-05", 0.23)
    first = via_reform_dict(reform)
    second = via_reform_dict(reform)
    for year in YEARS:
        assert annual(first, BASIC_RATE, year) == annual(second, BASIC_RATE, year)
    # Each simulation has its own parameter objects.
    assert first.tax_benefit_system.parameters.get_child(
        BASIC_RATE
    ) is not second.tax_benefit_system.parameters.get_child(BASIC_RATE)


# Differential: calendar-year changes give each changed parameter the annual
# values that editing the annualised parameters (the old reform-dict route)
# gave it. Blended and preserve_calendar_dates parameters are left out: the
# first are now day-weighted and the second never were annualised.


def legacy_annual(path, start, stop, value, year):
    parameters = tbs_module.processed_parameters().clone()
    parameters.get_child(path).update(
        start=instant_(start), stop=instant_(stop), value=value
    )
    return float(parameters.get_child(path)(f"{year}-01-01"))


from policyengine_core.periods import instant as instant_  # noqa: E402


@PROPERTY_SETTINGS
@given(
    path=st.sampled_from([BASIC_RATE, UC_SINGLE_OLD, PERSONAL_ALLOWANCE]),
    first=st.integers(2024, 2034),
    years=st.integers(1, 6),
    open_ended=st.booleans(),
    value=st.sampled_from([0.17, 450.0, 14_000]),
)
def test_calendar_year_changes_match_the_annualised_route(
    path, first, years, open_ended, value
):
    start = f"{first}-01-01"
    stop = FAR if open_ended else f"{first + years - 1}-12-31"
    simulation = via_reform_dict(as_dict(path, start, stop, value))
    for year in YEARS:
        if path == PERSONAL_ALLOWANCE and year > LAST_FROZEN_TAX_YEAR:
            # Editing the annualised parameters left the allowance on
            # current law's path after a change; prior law is statute instead,
            # indexing from the year before (cos d1344).
            expected = statutory_allowance([(_day(start), _day(stop), value)], year)
        else:
            expected = legacy_annual(path, start, stop, value, year)
        assert annual(simulation, path, year) == pytest.approx(expected), year


# More parameter kinds for the oracle: a boolean, a null-valued
# preserve_calendar_dates amount, and changes that start before a
# parameter's first stated value.

REBALANCING_ACTIVE = "gov.dwp.universal_credit.rebalancing.active"


@PROPERTY_SETTINGS
@given(
    start=st.dates(datetime.date(2010, 1, 1), datetime.date(2032, 12, 31)),
    length=st.integers(0, 2_000),
    value=st.booleans(),
)
def test_boolean_changes_match_the_oracle(start, length, value):
    stop = start + datetime.timedelta(days=length)
    simulation = via_reform_dict(as_dict(REBALANCING_ACTIVE, start, stop, value))
    expected = overlay(projected_entries(REBALANCING_ACTIVE), start, stop, value)
    for year in YEARS:
        assert bool(annual(simulation, REBALANCING_ACTIVE, year)) == bool(
            oracle_annual(expected, year, blend=False)
        ), year


@PROPERTY_SETTINGS
@given(
    start=st.dates(datetime.date(2025, 1, 1), datetime.date(2031, 12, 31)),
    length=st.integers(0, 900),
    value=st.sampled_from([400.0, 450.0]),
)
def test_preserve_calendar_dates_changes_keep_their_dates(start, length, value):
    # The protected LCWRA amount keeps statutory dates and holds nulls for
    # years not yet legislated.
    stop = start + datetime.timedelta(days=length)
    simulation = via_reform_dict(as_dict(PROTECTED_LCWRA, start, stop, value))
    expected = overlay(projected_entries(PROTECTED_LCWRA), start, stop, value)
    parameter = simulation.tax_benefit_system.parameters.get_child(PROTECTED_LCWRA)
    day = datetime.date(2024, 1, 1)
    while day < datetime.date(2035, 1, 1):
        assert parameter(day.isoformat()) == timeline_value(expected, day), day
        day += datetime.timedelta(days=37)


# Review round 3 (GPT-6.1 Sol): failed override batches roll back, and
# nodes a structural reform adds survive rebuilds and reprocessing.


class _add_bonus(Reform):
    def apply(self):
        from policyengine_core.parameters import ParameterNode

        self.parameters.add_child(
            "test_budget",
            ParameterNode("test_budget", data={"bonus": {"values": {"2000-01-01": 1}}}),
        )


def test_a_failed_override_batch_applies_none_of_its_overrides():
    simulation = Simulation(situation=SITUATION)
    system = simulation.tax_benefit_system
    parameters = system.parameters
    with pytest.raises(ValueError):
        Scenario.from_reform(
            {BASIC_RATE: {"2027": 0.3}, "gov.not_a_real_parameter": {"2027": 1}}
        ).apply(simulation)
    assert annual(simulation, BASIC_RATE, 2027) == 0.20
    assert system.legacy_overrides == []
    # An unknown path is refused before anything changes, and the tree is
    # the one the system had.
    assert system.parameters is parameters
    Scenario.from_reform({BASIC_RATE: {"2027": 0.3}}).apply(simulation)
    assert system.parameters is parameters
    assert annual(simulation, BASIC_RATE, 2027) == 0.3
    simulation.apply_parameter_changes({UC_SINGLE_OLD: {"2027": 500}})
    assert annual(simulation, BASIC_RATE, 2027) == 0.3
    assert annual(simulation, UC_SINGLE_OLD, 2027) == 500


def test_a_batch_failing_after_an_update_restores_values_and_flags(monkeypatch):
    simulation = Simulation(situation=SITUATION)
    system = simulation.tax_benefit_system
    rate = system.parameters.get_child(BASIC_RATE)
    values_list = rate.values_list
    # Processing marks parameters modified, so clear the flags on the path
    # to the rate to see whether a failed batch leaves them set.
    path, node = [], rate
    while node is not None:
        node.modified = False
        path.append(node)
        node = getattr(node, "parent", None)
    # Reform.from_dict keys reach the overrides unparsed, so the second
    # override fails after the first has updated the rate.
    reform = Reform.from_dict(
        {BASIC_RATE: {"2027-01-01": 0.3}, UC_SINGLE_OLD: {"not-a-date": 1}},
        country_id="uk",
    )
    # Guard against the test going empty: the batch must fail inside the
    # overrides, after the rate was updated, so the rollback runs.
    original = tbs_module.apply_legacy_overrides
    seen = {}

    def spy(parameters, overrides):
        try:
            return original(parameters, overrides)
        except Exception:
            seen["rate_updated"] = rate.values_list is not values_list
            raise

    monkeypatch.setattr(tbs_module, "apply_legacy_overrides", spy)
    with pytest.raises(ValueError):
        Scenario.from_reform(reform).apply(simulation)
    assert seen == {"rate_updated": True}
    assert rate.values_list is values_list
    assert annual(simulation, BASIC_RATE, 2027) == 0.20
    assert system.legacy_overrides == []
    assert not any(node.modified for node in path)


def test_a_rebuild_keeps_a_structural_reforms_parameter():
    simulation = Simulation(
        situation=SITUATION, reform=(_add_bonus, {"test_budget.bonus": 7})
    )
    simulation.apply_parameter_changes({BASIC_RATE: {"2027": 0.21}})
    parameters = simulation.tax_benefit_system.parameters
    assert parameters.test_budget.bonus("2027-01-01") == 7
    assert annual(simulation, BASIC_RATE, 2027) == 0.21
    # Repeated rebuilds keep it too.
    simulation.apply_parameter_changes({UC_SINGLE_OLD: {"2027": 500}})
    assert simulation.tax_benefit_system.parameters.test_budget.bonus("2027-01-01") == 7


def test_reprocessing_keeps_a_structural_reforms_parameter():
    from policyengine_uk.scenarios.no_economic_assumptions import (
        no_economic_assumptions,
    )

    simulation = Simulation(
        situation=SITUATION, reform=(_add_bonus, {"test_budget.bonus": 7})
    )
    no_economic_assumptions.apply(simulation)
    parameters = simulation.tax_benefit_system.parameters
    assert parameters.test_budget.bonus("2027-01-01") == 7
    assert annual(simulation, PERSONAL_ALLOWANCE, 2035) == 12_570
    assert simulation.tax_benefit_system._parameters_before_reset is None


def test_failed_reprocessing_leaves_the_system_as_it_was(monkeypatch):
    simulation = Simulation(situation=SITUATION)
    Scenario.from_reform({BASIC_RATE: {"2027": 0.3}}).apply(simulation)
    system = simulation.tax_benefit_system
    system.reset_parameters()
    reloaded = (system.parameters, system._projected_timelines, system._raw_parameters)

    # Fail after the rebuild has replaced the parameters, while replaying
    # the legacy override.
    def fail(*args, **kwargs):
        raise RuntimeError("replay failed")

    monkeypatch.setattr(tbs_module, "apply_legacy_overrides", fail)
    with pytest.raises(RuntimeError, match="replay failed"):
        system.process_parameters()
    assert system.parameters is reloaded[0]
    assert system._projected_timelines is reloaded[1]
    assert system._raw_parameters is reloaded[2]
    # The tree is as reloaded, not processed: no baseline child, and the
    # basic rate keeps its legal dates rather than fiscal-year values.
    assert "baseline" not in system.parameters.children
    # Processing again then works.
    monkeypatch.undo()
    system.process_parameters()
    assert "baseline" in system.parameters.children
    assert annual(simulation, BASIC_RATE, 2027) == 0.3


class _add_top_band(Reform):
    def apply(self):
        scale = self.parameters.gov.hmrc.income_tax.rates.uk
        band = scale.brackets[-1].clone()
        band.parent = scale
        scale.brackets.append(band)
        band.threshold.update(period="year:2000:200", value=200_000)
        band.rate.update(period="year:2000:200", value=0.5)


def test_a_rebuild_keeps_a_band_a_structural_reform_appended():
    simulation = Simulation(situation=SITUATION, reform=_add_top_band)
    # The scale has four bands, uk[0] to uk[3]; the reform adds uk[4].
    top = "gov.hmrc.income_tax.rates.uk[4].rate"
    assert annual(simulation, top, 2027) == 0.5
    simulation.apply_parameter_changes({BASIC_RATE: {"2027": 0.21}})
    assert annual(simulation, top, 2027) == 0.5
    assert annual(simulation, BASIC_RATE, 2027) == 0.21


def test_a_second_reset_keeps_the_processed_tree_for_grafting():
    simulation = Simulation(
        situation=SITUATION, reform=(_add_bonus, {"test_budget.bonus": 7})
    )
    system = simulation.tax_benefit_system
    system.reset_parameters()
    system.reset_parameters()
    system.process_parameters()
    assert system.parameters.test_budget.bonus("2027-01-01") == 7


def test_grafting_adds_only_missing_nodes():
    from policyengine_core.parameters import ParameterNode

    from policyengine_uk.utils.dated_reforms import graft_missing_nodes

    source = ParameterNode(
        "",
        data={
            "a": {
                "x": {"values": {"2000-01-01": 1}},
                "y": {"values": {"2000-01-01": 2}},
            },
            "baseline": {"z": {"values": {"2000-01-01": 3}}},
        },
    )
    target = ParameterNode("", data={"a": {"x": {"values": {"2000-01-01": 10}}}})
    added = graft_missing_nodes(source, target)
    assert added == ["a.y"]
    assert target.a.x("2001-01-01") == 10
    assert target.a.y("2001-01-01") == 2
    assert "baseline" not in target.children


def test_grafting_appends_missing_scale_brackets():
    from policyengine_core.parameters import ParameterNode

    from policyengine_uk.utils.dated_reforms import graft_missing_nodes

    def band(threshold, rate):
        return {
            "threshold": {"values": {"2000-01-01": threshold}},
            "rate": {"values": {"2000-01-01": rate}},
        }

    source = ParameterNode(
        "", data={"s": {"brackets": [band(0, 0.1), band(10, 0.2), band(20, 0.3)]}}
    )
    target = ParameterNode("", data={"s": {"brackets": [band(0, 0.15), band(10, 0.2)]}})
    assert graft_missing_nodes(source, target) == ["s[2]"]
    assert len(target.s.brackets) == 3
    assert target.s.brackets[0].rate("2001-01-01") == 0.15
    assert target.s.brackets[2].rate("2001-01-01") == 0.3
    assert target.s.brackets[2].parent is target.s


# pe-uk#2435: a change starting on a parameter's first stated date was
# backdated to the years before it.

NEW_CLAIMANT_HEALTH = "gov.dwp.universal_credit.rebalancing.new_claimant_health_element"
PER_CAPITA_GDP = "gov.economic_assumptions.yoy_growth.obr.per_capita.gdp"
OBR_RENT = "gov.economic_assumptions.yoy_growth.obr.rent"


@pytest.mark.parametrize(
    "route, reform",
    [
        ("reform_dict", {NEW_CLAIMANT_HEALTH: {"2026-01-01.2026-12-31": 300.0}}),
        ("reform_dict", {NEW_CLAIMANT_HEALTH: {"2026-01-01.2100-12-31": 300.0}}),
        ("parameter_changes", {NEW_CLAIMANT_HEALTH: {"2026-01-01.2026-12-31": 300.0}}),
        (
            "scenario_before_data_load",
            {NEW_CLAIMANT_HEALTH: {"2026-01-01.2026-12-31": 300.0}},
        ),
        # Reform.from_dict reads a bare year as from 1 January on: the first
        # stated date here.
        ("reform_from_dict", {NEW_CLAIMANT_HEALTH: {"2026": 300.0}}),
    ],
)
def test_a_change_from_a_parameters_first_date_leaves_earlier_years_alone(
    route, reform
):
    # The first stated value is £217.26 from 2026-01-01; the change from that
    # date set 2024 and 2025 to £300 too.
    simulation = ROUTES[route](reform)
    parameter = simulation.tax_benefit_system.parameters.get_child(NEW_CLAIMANT_HEALTH)
    current = tbs_module.processed_parameters().get_child(NEW_CLAIMANT_HEALTH)
    for day in ("2024-06-01", "2025-06-01"):
        assert parameter(day) == pytest.approx(current(day)), day
    assert parameter("2026-06-01") == 300.0


def test_backdating_extends_prior_laws_first_value_before_a_change_from_it():
    from policyengine_core.parameters import ParameterNode

    from policyengine_uk.utils.dated_reforms import (
        BACKDATED_FROM,
        ParameterAssignment,
        write_assignment,
    )
    from policyengine_uk.utils.parameters import (
        BACKDATED_VALUE,
        backdate_parameters,
    )

    def written(first, start, stop):
        node = ParameterNode("", data={"p": {"values": {first: 217.26}}})
        write_assignment(
            node.p, ParameterAssignment("p", instant_(start), instant_(stop), 300.0, 0)
        )
        return node

    node = written("2026-01-01", "2026-01-01", "2026-12-31")
    # Recorded, not written at BACKDATED_FROM: the generation steps between
    # this and backdating see the change as the first value.
    assert node.p.metadata[BACKDATED_VALUE] == 217.26
    assert min(entry.instant_str for entry in node.p.values_list) == "2026-01-01"
    backdate_parameters(node, BACKDATED_FROM)
    assert node.p("2015-06-01") == 217.26
    assert node.p("2025-06-01") == 217.26
    assert node.p("2026-06-01") == 300.0
    assert node.p("2027-06-01") == 217.26
    assert BACKDATED_VALUE not in node.p.metadata
    # A first date that is BACKDATED_FROM itself has nothing earlier to keep.
    earliest = written(BACKDATED_FROM, BACKDATED_FROM, "2015-12-31")
    assert BACKDATED_VALUE not in earliest.p.metadata
    backdate_parameters(earliest, BACKDATED_FROM)
    assert earliest.p("2015-06-01") == 300.0
    assert earliest.p("2016-06-01") == 217.26


@pytest.mark.parametrize("route", ["reform_dict", "parameter_changes"])
@pytest.mark.parametrize(
    "reform, year",
    [
        # From the first stated date, then a change ending before it.
        (
            {
                NEW_CLAIMANT_HEALTH: {
                    "2026-01-01.2100-12-31": 300.0,
                    "2024-01-01.2024-12-31": 100.0,
                }
            },
            2025,
        ),
        # From before it, then an earlier one.
        (
            {
                NEW_CLAIMANT_HEALTH: {
                    "2024-01-01.2100-12-31": 300.0,
                    "2020-01-01.2020-12-31": 100.0,
                }
            },
            2022,
        ),
    ],
)
def test_an_earlier_change_after_a_first_date_one_resumes_with_prior_law(
    route, reform, year
):
    simulation = ROUTES[route](reform)
    parameter = simulation.tax_benefit_system.parameters.get_child(NEW_CLAIMANT_HEALTH)
    current = tbs_module.processed_parameters().get_child(NEW_CLAIMANT_HEALTH)
    day = f"{year}-06-01"
    assert parameter(day) == pytest.approx(current(day))


written_dates = st.dates(datetime.date(2014, 1, 1), datetime.date(2030, 12, 31))


@st.composite
def timelines_and_changes(draw):
    """A timeline of 1-3 stated values and 1-3 changes written onto it."""
    stated = sorted(draw(st.sets(written_dates, min_size=1, max_size=3)))
    timeline = {day: float(draw(st.integers(1, 99))) for day in stated}
    changes = []
    for _ in range(draw(st.integers(1, 3))):
        start = draw(written_dates)
        stop = start + datetime.timedelta(days=draw(st.integers(0, 2_000)))
        changes.append((start, stop, float(draw(st.integers(100, 199)))))
    return timeline, changes


@settings(max_examples=300, deadline=None, derandomize=True)
@given(case=timelines_and_changes())
def test_writing_then_backdating_leaves_prior_law_outside_every_change(case):
    from policyengine_core.parameters import ParameterNode

    from policyengine_uk.utils.dated_reforms import (
        BACKDATED_FROM,
        ParameterAssignment,
        write_assignment,
    )
    from policyengine_uk.utils.parameters import backdate_parameters

    timeline, changes = case
    node = ParameterNode(
        "",
        data={"p": {"values": {str(day): value for day, value in timeline.items()}}},
    )
    for start, stop, value in changes:
        write_assignment(
            node.p,
            ParameterAssignment(
                "p", instant_(str(start)), instant_(str(stop)), value, 0
            ),
        )
    backdate_parameters(node, BACKDATED_FROM)

    first = min(timeline)

    def prior_law(day):
        stated = [d for d in timeline if d <= day]
        return timeline[max(stated)] if stated else timeline[first]

    day = _day(BACKDATED_FROM)
    while day <= datetime.date(2036, 12, 31):
        covering = [value for start, stop, value in changes if start <= day <= stop]
        expected = covering[-1] if covering else prior_law(day)
        assert node.p(str(day)) == expected, day
        day += datetime.timedelta(days=37)


def leaf_values(parameters, day):
    """Every parameter's value at ``day``, by name.

    Not the ``baseline`` copy, whose parameters keep the names of the ones it
    copies and would otherwise stand in for them.
    """
    return {
        parameter.name: parameter(day)
        for key, child in parameters.children.items()
        if key != "baseline"
        for parameter in (
            child.get_descendants() if isinstance(child, ParameterNode) else [child]
        )
        if isinstance(parameter, Parameter)
    }


@functools.lru_cache(maxsize=None)
def current_law_leaf_values(day):
    # An unreformed simulation's, which has the parameters a simulation adds
    # to the processed ones (the capital gains growth series).
    return leaf_values(
        Simulation(situation=SITUATION).tax_benefit_system.parameters, day
    )


def same_value(a, b):
    if isinstance(a, float) and isinstance(b, float):
        return a == b or abs(a - b) <= 1e-9 or (np.isnan(a) and np.isnan(b))
    return a == b


def parameters_differing_from_current_law(parameters, day):
    current = current_law_leaf_values(day)
    reformed = leaf_values(parameters, day)
    return sorted(
        name
        for name in current.keys() | reformed.keys()
        if name not in current
        or name not in reformed
        or not same_value(current[name], reformed[name])
    )


def stated_timelines():
    """Each statutory gov parameter's entries, oldest first, by name."""
    for parameter in tbs_module.statutory_parameters().get_descendants():
        if not isinstance(parameter, Parameter) or not parameter.values_list:
            continue
        # A few list-valued parameters are stated from 0000-01-01, which is
        # no date.
        if not parameter.name.startswith("gov.") or any(
            entry.instant_str < "0001" for entry in parameter.values_list
        ):
            continue
        yield (
            parameter.name,
            [
                (_day(entry.instant_str), entry.value)
                for entry in sorted(parameter.values_list, key=lambda e: e.instant_str)
            ],
        )


def statutory_entries(name):
    parameter = tbs_module.statutory_parameters().get_child(name)
    return sorted((_day(e.instant_str), e.value) for e in parameter.values_list)


# Per-capita GDP's index also feeds the capital gains series; rent's feeds
# no other generated series.
@pytest.mark.parametrize("series", [PER_CAPITA_GDP, OBR_RENT])
def test_current_laws_own_first_value_from_a_growth_series_first_year_changes_nothing(
    series,
):
    # Writing a growth series' own first value over its first year must leave
    # every parameter as it is. Writing prior law at BACKDATED_FROM instead of
    # recording it moved the series' index base year to 2015.
    (first, value), *_ = statutory_entries(series)
    simulation = via_reform_dict(
        as_dict(series, first, datetime.date(first.year, 12, 31), value)
    )
    parameters = simulation.tax_benefit_system.parameters
    for year in range(2015, 2040):
        day = f"{year}-01-01"
        assert parameters_differing_from_current_law(parameters, day) == [], year


# A change to a budget total rescales the population's spending on it
# (adjust_budgets), which a one-person situation has none of.
BUDGET_TOTALS = ("gov.dfe.education_spending", "gov.dhsc.spending", "gov.dft.spending")


@functools.lru_cache(maxsize=None)
def later_first_dated_parameters():
    """Numeric parameters first stated after the year before can be checked.

    Processing backdates a value first stated after 2015 to 2015, so a change
    on or near that first date is where a change could leak into earlier
    years; a first date within 2015 (or by 5 April 2016, for a fiscal-year
    parameter) leaves no earlier year to check.
    """
    calendar = tbs_module.parameter_reads_calendar_years()
    found = []
    for name, entries in stated_timelines():
        if name.startswith(BUDGET_TOTALS):
            continue
        (first, value), *_ = entries
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        earliest_checkable = (
            datetime.date(2015, 12, 31) if calendar(name) else datetime.date(2016, 4, 5)
        )
        if first > earliest_checkable:
            found.append((name, first, float(value)))
    return tuple(sorted(found))


def year_ends(name, year):
    """The last day of the year a parameter's annual value covers."""
    if tbs_module.parameter_reads_calendar_years()(name):
        return datetime.date(year, 12, 31)
    return datetime.date(year + 1, 4, 5)


@st.composite
def changes_around_a_first_date(draw):
    name, first, value = draw(st.sampled_from(later_first_dated_parameters()))
    # On the first date, or up to about two years either side of it.
    offset = draw(st.one_of(st.just(0), st.integers(-800, 800)))
    start = first + datetime.timedelta(days=offset)
    if draw(st.booleans()):
        stop = datetime.date(2100, 12, 31)
    else:
        stop = start + datetime.timedelta(days=draw(st.integers(0, 1_500)))
    route = draw(st.sampled_from(sorted(ROUTES)))
    # Twice the first stated value, or 1 for a first value of 0.
    return name, start, stop, value * 2 if value else 1.0, route


@PROPERTY_SETTINGS
@given(change=changes_around_a_first_date())
def test_no_change_reaches_a_year_before_it_starts(change):
    name, start, stop, value, route = change
    years = [
        year for year in range(2015, start.year + 1) if year_ends(name, year) < start
    ]
    assume(years)
    simulation = ROUTES[route](as_dict(name, start, stop, value))
    parameters = simulation.tax_benefit_system.parameters
    reformed = parameters.get_child(name)
    current = tbs_module.processed_parameters().get_child(name)
    for year in years:
        day = f"{year}-01-01"
        assert reformed(day) == pytest.approx(current(day), abs=1e-9), year
        # No other parameter moves in a year that ends before the change
        # starts either (generated ones included, such as an index read from
        # a growth series), by a fiscal year's end, the later of the two.
        if datetime.date(year + 1, 4, 5) < start:
            assert parameters_differing_from_current_law(parameters, day) == [], year


@functools.lru_cache(maxsize=None)
def parameters_with_a_closed_span():
    """Parameters with a stated value that a later stated value ends."""
    found = []
    for name, entries in stated_timelines():
        spans = [
            (begins, ends, value)
            for (begins, value), (ends, _) in zip(entries, entries[1:])
            if begins >= datetime.date(2010, 1, 1)
        ]
        if spans:
            found.append((name, tuple(spans)))
    return tuple(sorted(found))


@pytest.fixture(scope="module", autouse=True)
def release_parameter_caches():
    # Drop the current-law leaf values (one table for each day asked for) and
    # the parameter lists once this module's tests are done, instead of for
    # the rest of the test process.
    yield
    current_law_leaf_values.cache_clear()
    later_first_dated_parameters.cache_clear()
    parameters_with_a_closed_span.cache_clear()


@st.composite
def restatements(draw):
    """A parameter's own stated value, written over part of its span."""
    name, spans = draw(st.sampled_from(parameters_with_a_closed_span()))
    begins, ends, value = draw(st.sampled_from(spans))
    days = (ends - begins).days
    start = begins + datetime.timedelta(
        days=draw(st.one_of(st.just(0), st.integers(0, days - 1)))
    )
    stop = start + datetime.timedelta(
        days=draw(st.integers(0, (ends - start).days - 1))
    )
    # Scenario.parameter_changes types its values as numbers and booleans, so
    # a list-valued parameter (such as the Universal Credit capital sources)
    # is restated through the other routes only.
    routes = sorted(ROUTES)
    if not isinstance(value, (int, float, bool)):
        routes.remove("parameter_changes")
    route = draw(st.sampled_from(routes))
    return name, start, stop, value, route


@PROPERTY_SETTINGS
@given(change=restatements())
@example(
    change=(
        "gov.dwp.universal_credit.means_test.capital.person_sources",
        datetime.date(2013, 4, 29),
        datetime.date(2013, 4, 29),
        [],
        "reform_dict",
    )
)
def test_restating_a_parameters_own_value_changes_nothing(change):
    name, start, stop, value, route = change
    simulation = ROUTES[route](as_dict(name, start, stop, value))
    parameters = simulation.tax_benefit_system.parameters
    # Every other year, to keep the test quick: a leak spans years.
    for year in range(2015, 2040, 2):
        day = f"{year}-01-01"
        assert parameters_differing_from_current_law(parameters, day) == [], year


# #1436: construction annualises statutory writes; Scenario.apply intentionally
# retains its distinct direct-annualised-date contract.
@pytest.mark.parametrize("route", ["reform_dict", "parameter_changes"])
def test_future_1436_logged_write_detects_calendar_prefix_edit_and_public_rebuild_restores_it(
    route,
):
    from policyengine_uk.utils.dated_reforms import reform_modifiers_are_effective

    change = as_dict(VAT_STANDARD_RATE, "2041-04-06", "2042-04-05", 200.0)
    situation = adult(years=(2041, 2042))
    simulation = ROUTES[route](change, situation=situation)
    system = simulation.tax_benefit_system
    scenario = Scenario.from_reform(change)
    recorded = tuple(system.dated_assignments)
    assert any(
        entry.path == VAT_STANDARD_RATE and entry.value == 200 for entry in recorded
    )
    assert annual(simulation, VAT_STANDARD_RATE, 2041) == 200
    assert reform_modifiers_are_effective(scenario.dated_reforms, system)
    rate = system.parameters.get_child(VAT_STANDARD_RATE)
    rate.update(start=instant_("2041-01-01"), stop=instant_("2041-01-01"), value=999)
    assert annual(simulation, VAT_STANDARD_RATE, 2041) == 999
    assert rate("2041-01-02") == 200
    assert tuple(system.dated_assignments) == recorded
    # These points are outside the raw April-to-April write but inside the
    # corresponding annual label. The old effectiveness window misses them.
    assert not reform_modifiers_are_effective(scenario.dated_reforms, system)
    # Public statutory rebuild, not Scenario.apply's intentional annualised
    # override semantics. Its independent expected January value is200.
    simulation.apply_parameter_changes(change)
    assert annual(simulation, VAT_STANDARD_RATE, 2041) == 200
    assert system.parameters.get_child(VAT_STANDARD_RATE)("2041-12-31") == 200


def test_future_1436_scenario_apply_keeps_direct_annualised_dates(caplog):
    simulation = Simulation(situation=adult(years=(2041, 2042)))
    before = annual(simulation, VAT_STANDARD_RATE, 2041)
    with caplog.at_level("WARNING", logger="policyengine_uk.utils.scenario"):
        Scenario.from_reform(
            as_dict(VAT_STANDARD_RATE, "2041-04-06", "2042-04-05", 0.73)
        ).apply(simulation)
    assert any(
        record.name == "policyengine_uk.utils.scenario"
        and record.levelname == "WARNING"
        and record.getMessage()
        == (
            "Scenario.apply edits the built simulation's annualised parameters, "
            "so its dated reform keys are not annualised again. Pass the scenario "
            "when constructing the Simulation to apply them on the statutory timeline."
        )
        for record in caplog.records
    )
    rate = simulation.tax_benefit_system.parameters.get_child(VAT_STANDARD_RATE)
    assert rate("2041-01-01") == before
    assert rate("2041-04-06") == 0.73
    assert rate("2042-01-01") == 0.73
    assert rate("2042-04-06") != 0.73


def test_future_1436_failed_annualised_batch_restores_exact_saved_list_and_flags(
    monkeypatch,
):
    simulation = Simulation(situation=adult(years=(2041, 2042)))
    system = simulation.tax_benefit_system
    rate = system.parameters.get_child(BASIC_RATE)
    saved_list = rate.values_list
    before = rate("2041-01-01")
    path, node = [], rate
    while node is not None:
        node.modified = False
        path.append(node)
        node = getattr(node, "parent", None)
    reform = Reform.from_dict(
        {BASIC_RATE: {"2041-01-01": 0.73}, UC_SINGLE_OLD: {"not-a-date": 1}},
        country_id="uk",
    )
    original = tbs_module.apply_legacy_overrides
    observed = {}

    def spy(parameters, overrides):
        try:
            return original(parameters, overrides)
        except Exception:
            observed["updated_before_failure"] = rate.values_list is not saved_list
            raise

    monkeypatch.setattr(tbs_module, "apply_legacy_overrides", spy)
    with pytest.raises(ValueError):
        Scenario.from_reform(reform).apply(simulation)
    assert observed == {"updated_before_failure": True}
    assert rate.values_list is saved_list
    assert rate("2041-01-01") == before
    assert system.legacy_overrides == []
    assert not any(node.modified for node in path)
