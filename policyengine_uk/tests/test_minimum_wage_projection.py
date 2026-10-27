"""Minimum wage rates after the last one set (#2537).

Each rate is set by an amending S.I. (National Minimum Wage Regulations 2015
regs. 4, 4A and 5). Later years are a projection, not law: from the last rate
set, each rate rises each April with
gov.economic_assumptions.indices.earnings_uprating (the May-July growth in
average weekly earnings of the year before, rounded to 0.1 percentage points
and never negative) and is rounded to the nearest penny.

Invariants, from the year after the last rate set to 2040:

1. Projection: each rate is the last rate set times the index's growth since
   then, rounded to the nearest penny.
2. Floor: no projected rate is below the last rate set. (Year-on-year
   monotonicity and age ordering, 2015 to 2040, are properties 2 and 3 of
   test_minimum_wage_rates.)
3. The age thresholds do not move: 0, 18, 21, 23 and 25 in every year.
4. A rate set later takes precedence, and the projection continues from it.
5. Each rule that reads the national living wage follows its projection
   (differential against each rule's own statement): the ESA permitted work
   limit (16 x NLW up to the next 50p, ESA Regs 2008 reg. 45(4) and (9A)),
   the UC benefit cap earnings exception (16 x NLW x 52 / 12 in whole pounds a
   month, UC Regs 2013 regs. 82(1)(a) and 6(1A)(za)), the minimum_wage
   variable, and the Carer's Allowance earnings limit (16 x NLW up to the next
   pound).
"""

import datetime
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
import yaml
from policyengine_core.parameters.parameter_at_instant import ParameterAtInstant

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.tax_benefit_system import (
    process_parameter_tree,
    statutory_parameters,
)

PARAMETER_DIR = (
    Path(__file__).resolve().parent.parent / "parameters/gov/hmrc/minimum_wage"
)
THRESHOLDS = [0, 18, 21, 23, 25]
LAST_CHECKED = 2040


def _last_set(values):
    date, entry = max(
        (datetime.date.fromisoformat(str(d)), e) for d, e in values.items()
    )
    return date, float(entry["value"] if isinstance(entry, dict) else entry)


RAW = yaml.safe_load((PARAMETER_DIR / "non_apprentice.yaml").read_text())
LAST_BRACKET_RATES = [_last_set(b["amount"]["values"]) for b in RAW["brackets"]]
LAST_APPRENTICE_RATE = _last_set(
    yaml.safe_load((PARAMETER_DIR / "apprentice.yaml").read_text())["values"]
)
LAST_YEAR = max(date.year for date, _ in [*LAST_BRACKET_RATES, LAST_APPRENTICE_RATE])
PROJECTED = range(LAST_YEAR + 1, LAST_CHECKED + 1)


def _index(parameters, year):
    return parameters(
        f"{year}-01-01"
    ).gov.economic_assumptions.indices.earnings_uprating


def _projected(rate, parameters, base_year, year):
    growth = _index(parameters, year) / _index(parameters, base_year)
    return round(rate * growth / 0.01) * 0.01


@pytest.mark.parametrize("year", PROJECTED)
def test_rates_are_the_last_rate_set_uprated_by_earnings(year):
    """Invariants 1 to 3."""
    p = system.parameters
    scale = p(f"{year}-01-01").gov.hmrc.minimum_wage.non_apprentice
    assert list(scale.thresholds) == THRESHOLDS
    for (date, rate), amount in zip(LAST_BRACKET_RATES, scale.amounts):
        expected = _projected(rate, p, date.year, year)
        assert amount == pytest.approx(expected, abs=1e-9), (year, rate)
        assert amount >= rate
    date, rate = LAST_APPRENTICE_RATE
    apprentice = p(f"{year}-01-01").gov.hmrc.minimum_wage.apprentice
    assert apprentice == pytest.approx(_projected(rate, p, date.year, year), abs=1e-9)
    assert apprentice >= rate


def test_april_2027_national_living_wage_follows_may_to_july_2026_earnings():
    """May-July 2026 average weekly earnings grew 3.9% (ONS KAC3, 20 October
    2026), so the April 2027 national living wage is £12.71 x 1.039 =
    £13.2057, £13.21 to the nearest penny."""
    p = system.parameters
    assert p("2027-01-01").gov.economic_assumptions.yoy_growth.earnings_uprating == (
        pytest.approx(0.039)
    )
    assert p("2026-01-01").gov.hmrc.minimum_wage.non_apprentice.amounts[-1] == 12.71
    assert p("2027-01-01").gov.hmrc.minimum_wage.non_apprentice.amounts[-1] == (
        pytest.approx(13.21, abs=1e-9)
    )


def test_a_rate_set_later_takes_precedence_and_the_projection_continues():
    """Invariant 4: a national living wage of £13.20 from 1 April 2027, added
    as a rate set by an S.I. would be, holds in 2027-28, and 2028-29 is £13.20
    times that April's earnings growth. The Carer's Allowance earnings limit
    follows it: 16 x £13.20 = £211.20, rounded up to £212."""
    tree = statutory_parameters()
    scale = tree.gov.hmrc.minimum_wage.non_apprentice
    for bracket in scale.brackets[2:]:
        amount = bracket.amount
        amount.values_list.append(
            ParameterAtInstant(amount.name, "2027-04-01", data=13.20)
        )
        amount.values_list.sort(key=lambda entry: entry.instant_str, reverse=True)
    tree, _ = process_parameter_tree(tree)

    def wage(year):
        return tree(f"{year}-01-01").gov.hmrc.minimum_wage.non_apprentice

    assert wage(2026).amounts[-1] == 12.71
    assert wage(2027).amounts[-1] == pytest.approx(13.20, abs=1e-9)
    for year in range(2028, 2031):
        assert wage(year).amounts[-1] == pytest.approx(
            _projected(13.20, tree, 2027, year), abs=1e-9
        ), year
    # The younger bands keep their own last rates' projection.
    assert wage(2027).amounts[0] == pytest.approx(
        system.parameters("2027-01-01").gov.hmrc.minimum_wage.non_apprentice.amounts[0]
    )

    def limit(year):
        return tree(f"{year}-01-01").gov.dwp.carers_allowance.earnings_limit

    assert limit(2026) == 204
    assert limit(2027) == 212


def _round_up_to_50p(amount):
    return math.ceil(Fraction(str(amount)) * 2) / 2


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_rules_that_read_the_national_living_wage_follow_its_projection():
    """Invariant 5, in every projected year to 2040."""
    years = list(PROJECTED)
    simulation = Simulation(
        situation={
            "people": {"adult": {"age": {str(year): 30 for year in years}}},
            "benunits": {"benunit": {"members": ["adult"]}},
            "households": {"household": {"members": ["adult"]}},
        }
    )
    parameters = simulation.tax_benefit_system.parameters
    for year in years:
        p = parameters(f"{year}-01-01")
        wage = p.gov.hmrc.minimum_wage.non_apprentice.amounts[-1]
        exact = Fraction(str(round(wage, 2)))
        assert simulation.calculate("minimum_wage", year)[0] == pytest.approx(wage)
        assert simulation.calculate("esa_exempt_work_higher_earnings_limit", year)[
            0
        ] == _round_up_to_50p(16 * exact), year
        monthly = math.floor(16 * exact * 52 / 12)
        assert simulation.calculate(
            "uc_benefit_cap_earnings_exception_threshold", year
        )[0] == pytest.approx(monthly * 12), year
        assert p.gov.dwp.carers_allowance.earnings_limit == math.ceil(16 * exact), year
