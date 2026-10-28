"""Minimum wage rates after the last one set (#2537).

Each rate is set by an amending S.I. (National Minimum Wage Regulations 2015
regs. 4, 4A and 5). Later years are a projection, not law: from the last rate
set, each rate rises each April with
gov.economic_assumptions.indices.earnings_uprating (the May-July growth in
average weekly earnings of the year before, rounded to 0.1 percentage points
and never negative) and is rounded to the nearest penny.

Invariants, from the year after each rate's last one set to 2040:

1. Projection: each rate is the last rate set times the index's growth since
   then, rounded to the nearest penny (once, not each April).
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
   variable for each age band, and the Carer's Allowance earnings limit (16 x
   NLW up to the next pound).
6. A reform's rate is not projected (intended, as for other uprated
   parameters): a rate a reform sets for one fiscal year leaves later years on
   the baseline's path, and one set from a year onwards holds flat.
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
FIRST_LAST_YEAR = min(
    date.year for date, _ in [*LAST_BRACKET_RATES, LAST_APPRENTICE_RATE]
)
# Years after every rate's last one set: the national living wage is projected.
PROJECTED = range(LAST_YEAR + 1, LAST_CHECKED + 1)
NLW = "gov.hmrc.minimum_wage.non_apprentice[{}].amount"


def _index(parameters, year):
    return parameters(
        f"{year}-01-01"
    ).gov.economic_assumptions.indices.earnings_uprating


def _projected(rate, parameters, base_year, year):
    growth = _index(parameters, year) / _index(parameters, base_year)
    return round(rate * growth / 0.01) * 0.01


@pytest.mark.parametrize("year", range(FIRST_LAST_YEAR + 1, LAST_CHECKED + 1))
def test_rates_are_the_last_rate_set_uprated_by_earnings(year):
    """Invariants 1 to 3, for each rate in the years after its own last one
    set."""
    p = system.parameters
    scale = p(f"{year}-01-01").gov.hmrc.minimum_wage.non_apprentice
    assert list(scale.thresholds) == THRESHOLDS
    apprentice = p(f"{year}-01-01").gov.hmrc.minimum_wage.apprentice
    pairs = [
        *zip(LAST_BRACKET_RATES, scale.amounts),
        (LAST_APPRENTICE_RATE, apprentice),
    ]
    for (date, rate), amount in pairs:
        if year <= date.year:
            continue
        expected = _projected(rate, p, date.year, year)
        assert amount == pytest.approx(expected, abs=1e-9), (year, rate)
        assert amount >= rate


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
    """Invariant 4: a national living wage of £13.50 from 1 April 2027, added
    as a rate set by an S.I. would be, holds in 2027-28, and later years are
    £13.50 times the earnings growth since. The Carer's Allowance earnings
    limit follows it: 16 x £13.50 = £216 (the projection alone gives £212)."""
    tree = statutory_parameters()
    scale = tree.gov.hmrc.minimum_wage.non_apprentice
    for bracket in scale.brackets[2:]:
        amount = bracket.amount
        amount.values_list.append(
            ParameterAtInstant(amount.name, "2027-04-01", data=13.50)
        )
        amount.values_list.sort(key=lambda entry: entry.instant_str, reverse=True)
    tree, _ = process_parameter_tree(tree)

    def wage(year):
        return tree(f"{year}-01-01").gov.hmrc.minimum_wage.non_apprentice

    assert wage(2026).amounts[-1] == 12.71
    assert wage(2027).amounts[-1] == pytest.approx(13.50, abs=1e-9)
    for year in range(2028, 2031):
        assert wage(year).amounts[-1] == pytest.approx(
            _projected(13.50, tree, 2027, year), abs=1e-9
        ), year
    # Adding a national living wage rate leaves the younger bands' projection
    # unchanged.
    assert wage(2027).amounts[0] == pytest.approx(
        system.parameters("2027-01-01").gov.hmrc.minimum_wage.non_apprentice.amounts[0]
    )

    def limit(year):
        return tree(f"{year}-01-01").gov.dwp.carers_allowance.earnings_limit

    assert limit(2026) == 204
    assert limit(2027) == 216


def _round_up_to_50p(amount):
    return math.ceil(Fraction(str(amount)) * 2) / 2


# One person in each age band, the national living wage's first.
AGES = {"adult": 30, "aged_23": 23, "aged_21": 21, "aged_19": 19, "aged_16": 16}
BANDS = {"adult": 4, "aged_23": 3, "aged_21": 2, "aged_19": 1, "aged_16": 0}


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_rules_that_read_the_national_living_wage_follow_its_projection():
    """Invariant 5, in every projected year to 2040."""
    years = list(PROJECTED)
    simulation = Simulation(
        situation={
            "people": {
                name: {"age": {str(year): age for year in years}}
                for name, age in AGES.items()
            },
            "benunits": {f"{name}_unit": {"members": [name]} for name in AGES},
            "households": {"household": {"members": list(AGES)}},
        }
    )
    parameters = simulation.tax_benefit_system.parameters
    for year in years:
        p = parameters(f"{year}-01-01")
        amounts = p.gov.hmrc.minimum_wage.non_apprentice.amounts
        wage = amounts[-1]
        exact = Fraction(str(round(wage, 2)))
        minimum_wage = simulation.calculate("minimum_wage", year)
        for index, name in enumerate(AGES):
            assert minimum_wage[index] == pytest.approx(amounts[BANDS[name]]), (
                year,
                name,
            )
        assert simulation.calculate("esa_exempt_work_higher_earnings_limit", year)[
            0
        ] == _round_up_to_50p(16 * exact), year
        monthly = math.floor(16 * exact * 52 / 12)
        assert simulation.calculate(
            "uc_benefit_cap_earnings_exception_threshold", year
        )[0] == pytest.approx(monthly * 12), year
        assert p.gov.dwp.carers_allowance.earnings_limit == math.ceil(16 * exact), year


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_a_reform_rate_is_not_projected():
    """Invariant 6 (intended): £13.50 for 2027-28 alone leaves 2028-29 on
    the baseline's path, where projecting from the reform's rate would give
    £13.50 x 1.024. £13.50 from 6 April 2027 onwards documents the disclosed
    behaviour rather than testing projection: the reform sets every year to
    2100, so nothing is left to project, and the baseline passes it."""
    baseline = system.parameters
    one_year = {NLW.format(b): {"2027": 13.50} for b in (2, 3, 4)}
    onwards = {NLW.format(b): {"2027-04-06.2100-12-31": 13.50} for b in (2, 3, 4)}

    def wages(parameters):
        return {
            year: parameters(
                f"{year}-01-01"
            ).gov.hmrc.minimum_wage.non_apprentice.amounts[-1]
            for year in range(2026, LAST_CHECKED + 1)
        }

    base = wages(baseline)
    for reform, later in ((one_year, base), (onwards, None)):
        reformed = wages(
            Simulation(
                situation={"people": {"adult": {"age": {"2027": 30}}}}, reform=reform
            ).tax_benefit_system.parameters
        )
        assert reformed[2026] == base[2026]
        assert reformed[2027] == pytest.approx(13.50)
        for year in range(2028, LAST_CHECKED + 1):
            expected = base[year] if later is base else 13.50
            assert reformed[year] == pytest.approx(expected), year
    assert base[LAST_CHECKED] > 13.50
