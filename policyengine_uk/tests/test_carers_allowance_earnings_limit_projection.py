"""Carer's Allowance earnings limit after its last legislated amount.

Reg. 8(1) of the Social Security (Invalid Care Allowance) Regulations 1976
states the limit as a fixed sum, which the up-rating regulations replace each
year. From April 2025 the Government sets it at 16 times the hourly national
living wage, rounded up to the nearest pound, "from April 2025 and in future
years" (Explanatory Memorandum to SI 2025/352, paragraph 5.6): £196 from April
2025 and £204 from April 2026 (SI 2026/218, Explanatory Memorandum paragraph
5.3). The model projects the years after the last legislated amount the same
way, from its own national living wage.

Invariants, for every national living wage path and hours value:

1. Statutory precedence: each year up to the last legislated amount reads the
   amount earnings_limit.yaml states for it, whatever the wage.
2. The rule reproduces the legislated amounts from the legislated wages:
   ceil(16 x £12.21) = £196 and ceil(16 x £12.71) = £204.
3. Rule: a projected year is ceil(hours x the national living wage in force on
   30 April), whatever the years before it were. A reform that lowers the
   wage or the hours lowers the limit, and one that changes a single year
   changes that year only.
4. Floor: while the national living wage is at least its April 2026 rate and
   the hours at least 16, no projected year is below the last legislated
   amount. The model's own projection never takes the wage below that rate.
5. Exact pounds (differential against exact arithmetic): a wage at which the
   hours come to a whole number of pounds, such as 16 x £13.25 = £212, gives
   that number, not one more, for every wage in whole pence however the float
   holds it.
6. The entitlement test reads the projected limit.
7. The baseline copy of the parameters keeps current law's limit under a
   reform.
"""

import datetime
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
import yaml
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.parameters.gov.dwp.carers_allowance.create_earnings_limit_projection import (
    national_living_wage_limit,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

LIMIT_FILE = (
    Path(__file__).parents[1]
    / "parameters/gov/dwp/carers_allowance/earnings_limit.yaml"
)
# (date, amount) for each amount the up-rating regulations set.
LIMIT_VALUES = sorted(
    (
        date if isinstance(date, datetime.date) else datetime.date.fromisoformat(date),
        entry["value"] if isinstance(entry, dict) else entry,
    )
    for date, entry in yaml.safe_load(LIMIT_FILE.read_text())["values"].items()
)
LAST_DATE, LAST_LIMIT = LIMIT_VALUES[-1]
LAST_YEAR = LAST_DATE.year
FIRST_PROJECTED = LAST_YEAR + 1
LAST_CHECKED = 2040
# The adult brackets (21 to 22, 23 to 24, 25 and over): the national living
# wage since April 2024.
NLW_BRACKETS = (2, 3, 4)
# The national living wage in force when the last amount was legislated
# (£12.71 from April 2026), in pence.
LAST_WAGE_PENCE = 1_271
HOURS = 16
WEEKS = 52

SITUATION = {"people": {"carer": {"age": {"2026": 45}}}}


def _wage_reform(wages, brackets=NLW_BRACKETS):
    """Set the national living wage for each fiscal {year: wage}."""
    return {
        f"gov.hmrc.minimum_wage.non_apprentice[{bracket}].amount": {
            str(year): wage for year, wage in wages.items()
        }
        for bracket in brackets
    }


def _parameters(reform=None):
    return Simulation(situation=SITUATION, reform=reform).tax_benefit_system.parameters


def _paths(reform=None, years=range(2015, LAST_CHECKED + 1), parameters=None):
    """Each year's earnings limit and national living wage, as the model
    reads them for that (fiscal) year."""
    if parameters is None:
        parameters = _parameters(reform)
    limits, wages, hours = {}, {}, {}
    for year in years:
        p = parameters(f"{year}-01-01")
        limits[year] = p.gov.dwp.carers_allowance.earnings_limit
        wages[year] = p.gov.hmrc.minimum_wage.non_apprentice.amounts[-1]
        if year >= 2025:
            hours[year] = (
                p.gov.dwp.carers_allowance.earnings_limit_national_living_wage_hours
            )
    return limits, wages, hours


def _stated_limit(year):
    """The amount earnings_limit.yaml sets for the year: in force on 30 April."""
    return [v for d, v in LIMIT_VALUES if d <= datetime.date(year, 4, 30)][-1]


def _rule(hours, wage):
    """ceil(hours x wage) in exact arithmetic, on the wage in whole pence: a
    rate is set in pence, and uprating can hold £14.45 as 14.450000000000001,
    which exactly x 20 would round up to £290 rather than £289."""
    return math.ceil(Fraction(str(hours)) * Fraction(str(round(wage, 2))))


def _check_invariants(limits, wages, hours):
    """Invariants 1, 3 and 4."""
    for year in range(2015, FIRST_PROJECTED):
        assert limits[year] == _stated_limit(year), year
    for year in range(FIRST_PROJECTED, LAST_CHECKED + 1):
        assert limits[year] == _rule(hours[year], wages[year]), (year, wages[year])
        if wages[year] >= LAST_WAGE_PENCE / 100 and hours[year] >= HOURS:
            assert limits[year] >= LAST_LIMIT, year


def test_the_rule_reproduces_the_legislated_amounts():
    """Invariant 2: the Explanatory Memoranda's rule gives the amounts the
    regulations set, from the national living wage in force each April."""
    limits, wages, hours = _paths(years=range(2024, 2027))
    assert wages[2025] == 12.21 and wages[2026] == 12.71
    assert hours[2025] == hours[2026] == 16
    for year in (2025, 2026):
        assert national_living_wage_limit(16, wages[year]) == limits[year]
    assert limits[2025] == 196 and limits[2026] == 204


def test_baseline_projection_follows_the_model_national_living_wage():
    """Invariants 1, 3 and 4 on the model's own projection, whatever its
    national living wage path is. That path never falls below the April 2026
    rate, so no projected year is below £204."""
    limits, wages, hours = _paths()
    _check_invariants(limits, wages, hours)
    for year in range(FIRST_PROJECTED, LAST_CHECKED + 1):
        assert wages[year] >= LAST_WAGE_PENCE / 100, year
        assert limits[year] >= LAST_LIMIT, year


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    legislated=st.lists(st.integers(1_000, 2_000), min_size=2, max_size=2),
    projected=st.lists(st.integers(LAST_WAGE_PENCE, 2_000), min_size=4, max_size=4),
)
# A rising path that hits whole pounds: 16 x £13.25 = £212 and 16 x £13.50 =
# £216 exactly, which must not round up to £213 and £217.
@example(legislated=[1_221, 1_271], projected=[1_325, 1_350, 1_375, 1_400])
# A path that rises and falls back to the April 2026 rate: the limit follows
# it down to £204 and no further.
@example(legislated=[1_221, 1_271], projected=[1_400, 1_271, 1_300, 1_271])
# Wages below the legislated ones in the legislated years change nothing there.
@example(legislated=[1_000, 1_000], projected=[1_300, 1_300, 1_300, 1_300])
def test_projection_follows_any_national_living_wage_path(legislated, projected):
    """Invariants 1, 3 and 4 for any national living wage in 2025 and 2026 and
    any at or above the April 2026 rate in 2027 to 2030: each projected year
    is ceil(16 x the wage) and none is below £204. Later years take the
    model's own wage again."""
    wages = [p / 100 for p in legislated + projected]
    reform = _wage_reform(dict(zip(range(2025, 2031), wages)))
    limits, model_wages, hours = _paths(reform)
    for year, wage in zip(range(2025, 2031), wages):
        assert model_wages[year] == pytest.approx(wage), year
    _check_invariants(limits, model_wages, hours)
    for year in range(FIRST_PROJECTED, LAST_CHECKED + 1):
        assert limits[year] >= LAST_LIMIT, year
    for year, p in zip(range(FIRST_PROJECTED, 2031), projected):
        assert limits[year] == math.ceil(Fraction(HOURS * p, 100)), year


def test_reforms_lower_the_limit_and_change_only_their_own_years():
    """Invariants 3 and 7, and which wage the rule reads.

    - 12 hours in 2027-28 and 20 hours in 2028-29 only.
    - A national living wage of £12.00 in 2029-30, below the April 2026 rate.
    - £14.50 for the 25 and over band alone in 2030-31: the rule reads that
      band, the last.
    Each year takes the rule from that year's own hours and wage, so the limit
    falls below £204 in 2027-28 and 2029-30 and returns to the model's path
    after 2030-31. The baseline copy keeps current law's limit throughout."""
    reform = _wage_reform({2029: 12.00})
    reform["gov.hmrc.minimum_wage.non_apprentice[4].amount"]["2030"] = 14.50
    reform["gov.dwp.carers_allowance.earnings_limit_national_living_wage_hours"] = {
        "2027": 12,
        "2028": 20,
    }
    parameters = _parameters(reform)
    limits, wages, hours = _paths(parameters=parameters)
    current_law, current_wages, _ = _paths()
    _check_invariants(limits, wages, hours)
    assert hours[2027] == 12 and hours[2028] == 20 and hours[2029] == 16
    assert limits[2027] == _rule(12, current_wages[2027]) < LAST_LIMIT
    assert limits[2028] == _rule(20, current_wages[2028])
    assert limits[2029] == 192
    assert wages[2030] == 14.50
    adult_bands = parameters("2030-01-01").gov.hmrc.minimum_wage.non_apprentice
    assert adult_bands.amounts[2] == current_wages[2030]
    assert limits[2030] == 232
    for year in range(2031, LAST_CHECKED + 1):
        assert limits[year] == current_law[year], year
    baseline = parameters.baseline.gov.dwp.carers_allowance.earnings_limit
    for year in range(2015, LAST_CHECKED + 1):
        assert baseline(f"{year}-04-30") == current_law[year], year


def test_hours_change_only_projected_years():
    """Invariants 1 and 3 for the hours: 20 hours from 2025 on leaves 2025
    and 2026 at their legislated amounts and sets every later year."""
    reform = {
        "gov.dwp.carers_allowance.earnings_limit_national_living_wage_hours": {
            "2025-01-01.2100-12-31": 20
        }
    }
    limits, wages, hours = _paths(reform)
    assert limits[2025] == 196 and limits[2026] == 204
    assert hours[FIRST_PROJECTED] == 20
    _check_invariants(limits, wages, hours)
    assert limits[FIRST_PROJECTED] == math.ceil(
        Fraction(20) * Fraction(str(wages[FIRST_PROJECTED]))
    )


@pytest.mark.parametrize("representation", ["divided", "multiplied"])
def test_whole_pounds_are_exact_for_every_wage_in_pence(representation):
    """Invariant 5, exhaustively for wages from 1p to £50 and 1 to 40 hours,
    against exact arithmetic. "multiplied" holds the wage as uprating's
    rounding does (pence x 0.01). The product can then sit just above the
    exact amount: 20 x (1,020 x 0.01) is 204.00000000000003."""
    assert 20 * (1_020 * 0.01) > 204
    for hours in range(1, 41):
        for p in range(1, 5_001):
            wage = p / 100 if representation == "divided" else p * 0.01
            expected = math.ceil(Fraction(hours * p, 100))
            assert national_living_wage_limit(hours, wage) == expected, (hours, p)


def test_entitlement_reads_the_projected_limit():
    """Invariant 6: a national living wage of £13.50 from April 2028 gives a
    limit of £216 (16 x £13.50, a whole number of pounds). Earnings of £216 a
    week are within it and £217 over it."""
    year = 2028
    reform = _wage_reform({year: 13.50})
    simulation = Simulation(
        situation={
            "people": {
                name: {
                    "age": {year: 45},
                    "care_hours": {year: 40},
                    "carers_allowance_earnings": {year: WEEKS * weekly},
                }
                for name, weekly in (("within", 216), ("over", 217))
            },
            "benunits": {
                "within": {"members": ["within"]},
                "over": {"members": ["over"]},
            },
            "households": {
                "within": {"members": ["within"], "country": {year: "ENGLAND"}},
                "over": {"members": ["over"], "country": {year: "ENGLAND"}},
            },
        },
        reform=reform,
    )
    parameters = simulation.tax_benefit_system.parameters(f"{year}-01-01")
    assert parameters.gov.dwp.carers_allowance.earnings_limit == 216
    gainful = simulation.calculate("is_gainfully_employed_for_carers_allowance", year)
    assert list(np.asarray(gainful, dtype=bool)) == [False, True]
    allowance = simulation.calculate("carers_allowance", year)
    assert allowance[0] > 0 and allowance[1] == 0
