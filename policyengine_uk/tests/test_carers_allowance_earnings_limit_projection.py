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
3. Floor: no projected year is below the last legislated amount, nor below
   the year before it.
4. Rule: a projected year is ceil(hours x the national living wage in force on
   30 April), unless that is below the year before's limit, which then holds.
   Holding is intended: the limit has never been cut, and the rule is stated
   for wages that rise. For a wage path that never falls below the last
   legislated wage, every projected year equals the rule.
5. Exact pounds (differential against exact arithmetic): a wage at which the
   hours come to a whole number of pounds, such as 16 x £13.25 = £212, gives
   that number, not one more.
6. The entitlement test reads the projected limit.
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
WEEKS = 52

SITUATION = {"people": {"carer": {"age": {"2026": 45}}}}


def _wage_reform(wages):
    """Set the national living wage for each {year: wage}."""
    return {
        f"gov.hmrc.minimum_wage.non_apprentice[{bracket}].amount": {
            str(year): wage for year, wage in wages.items()
        }
        for bracket in NLW_BRACKETS
    }


def _paths(reform=None, years=range(2015, LAST_CHECKED + 1)):
    """Each year's earnings limit and national living wage, as the model
    reads them for that (fiscal) year."""
    parameters = Simulation(
        situation=SITUATION, reform=reform
    ).tax_benefit_system.parameters
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


def _check_invariants(limits, wages, hours):
    for year in range(2015, FIRST_PROJECTED):
        assert limits[year] == _stated_limit(year), year
    for year in range(FIRST_PROJECTED, LAST_CHECKED + 1):
        rule = math.ceil(Fraction(str(hours[year])) * Fraction(str(wages[year])))
        assert limits[year] >= LAST_LIMIT, year
        assert limits[year] >= limits[year - 1], year
        assert limits[year] == max(limits[year - 1], rule), (year, wages[year])


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
    national living wage path is."""
    _check_invariants(*_paths())


pence = st.integers(min_value=1_000, max_value=2_000)


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(wages=st.lists(pence, min_size=6, max_size=6))
# A rising path that hits whole pounds: 16 x £13.25 = £212 and 16 x £13.50 =
# £216 exactly, which must not round up to £213 and £217.
@example(wages=[1_221, 1_271, 1_325, 1_350, 1_375, 1_400])
# A wage that falls after 2027: the limit holds at £212 rather than falling.
@example(wages=[1_221, 1_271, 1_325, 1_200, 1_000, 1_400])
# Wages below the legislated ones in the legislated years change nothing there.
@example(wages=[1_000, 1_000, 1_300, 1_300, 1_300, 1_300])
def test_projection_follows_any_national_living_wage_path(wages):
    """Invariants 1, 3 and 4 for a reformed wage in 2025 to 2030. Later years
    take the model's own wage again."""
    reform = _wage_reform({year: p / 100 for year, p in zip(range(2025, 2031), wages)})
    limits, model_wages, hours = _paths(reform)
    for year, p in zip(range(2025, 2031), wages):
        assert model_wages[year] == pytest.approx(p / 100), year
    _check_invariants(limits, model_wages, hours)
    # A path that never falls below the last legislated wage follows the rule
    # in every year it sets.
    path = [12.71] + [p / 100 for p in wages[2:]]
    if all(later >= earlier for earlier, later in zip(path, path[1:])):
        for year, p in zip(range(FIRST_PROJECTED, 2031), wages[2:]):
            assert limits[year] == math.ceil(Fraction(16 * p, 100)), year


def test_hours_change_only_projected_years():
    """Invariant 1 and 4 for the hours: 20 hours from 2027 at the model's wage
    leaves 2025 and 2026 at their legislated amounts."""
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
    rounding does (pence x 0.01), which can sit just above the exact amount:
    1,325 x 0.01 is 13.250000000000002."""
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
