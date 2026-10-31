"""Minimum wage rates after the last one set (#2537).

Each rate is set by an amending S.I. (National Minimum Wage Regulations 2015
regs. 4, 4A and 5); the April 2027 rates are the ones Budget 2026 announced
(paragraph 6.128), ahead of their S.I. Later years are a projection, not law:
from the last rate set, each rate rises each April with
gov.economic_assumptions.indices.obr.national_living_wage (the OBR's forecast
of the national living wage, EFO economy Table 1.13, to the end of the EFO,
then average earnings growth) and is rounded to the nearest penny.

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
from policyengine_uk.utils.import_obr_forecasts import compute_level_growth

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
NLW = "gov.hmrc.minimum_wage.non_apprentice[{}].amount"


def _index(parameters, year):
    return parameters(
        f"{year}-01-01"
    ).gov.economic_assumptions.indices.obr.national_living_wage


def _projected(rate, parameters, base_year, year):
    growth = _index(parameters, year) / _index(parameters, base_year)
    return round(rate * growth / 0.01) * 0.01


@pytest.mark.parametrize("year", range(FIRST_LAST_YEAR + 1, LAST_CHECKED + 1))
def test_rates_are_the_last_rate_set_uprated_by_the_index(year):
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


# OBR EFO October 2026, detailed forecast tables (economy), Table 1.13: the
# national living wage in April of each year, £ an hour. "The NLW has been set
# by the Government up until 2027 ... Figures beyond 2027 are OBR estimates
# consistent with the rest of our economy forecast." The table is also in
# tests/fixtures/obr_economy, which the importer reads.
OBR_NATIONAL_LIVING_WAGE = {
    2020: 8.72,
    2021: 8.91,
    2022: 9.5,
    2023: 10.42,
    2024: 11.44,
    2025: 12.21,
    2026: 12.71,
    2027: 13.21,
    2028: 13.513623297578135,
    2029: 13.854853379339588,
    2030: 14.23293930734993,
    2031: 14.617023376183901,
}
GROWTH = yaml.safe_load(
    (PARAMETER_DIR.parents[1] / "economic_assumptions/yoy_growth.yaml").read_text()
)["obr"]


def _growth(series, year):
    return GROWTH[series]["values"][datetime.date(year, 1, 1)]


def test_the_series_reproduces_the_obr_table():
    """Differential against the published table. The growth series is each
    year's rate over the year before's, to six decimals, from 2021 to the end
    of the EFO, and the model's national living wage in each April is the
    table's, rounded to the nearest penny: the rates set to 2027 (£13.21 from
    Budget 2026), then the OBR's estimates of £13.51, £13.85, £14.23 and
    £14.62 from 2028 to 2031."""
    p = system.parameters
    for year in range(2021, max(OBR_NATIONAL_LIVING_WAGE) + 1):
        expected = OBR_NATIONAL_LIVING_WAGE[year] / OBR_NATIONAL_LIVING_WAGE[year - 1]
        assert _growth("national_living_wage", year) == pytest.approx(
            round(expected - 1, 6), abs=1e-12
        ), year
    for year, rate in OBR_NATIONAL_LIVING_WAGE.items():
        wage = p(f"{year}-01-01").gov.hmrc.minimum_wage.non_apprentice.amounts[-1]
        assert wage == pytest.approx(round(rate, 2), abs=1e-9), year


TABLE_1_13 = (
    Path(__file__).parent
    / "fixtures/obr_economy/efo_october_2026_economy_table_1_13.xlsx"
)


def test_the_table_here_is_the_one_the_importer_reads():
    """OBR_NATIONAL_LIVING_WAGE is Table 1.13 as the importer reads it from
    the real October 2026 workbook, so a refreshed fixture fails here until
    the table here moves with it."""
    line = compute_level_growth(TABLE_1_13.read_bytes())[("national_living_wage",)].line
    assert line.levels == OBR_NATIONAL_LIVING_WAGE
    assert line.set_until == 2027


def test_the_index_carries_any_year_of_the_table_to_any_later_year():
    """Invariants of the series: the national living wage index is above
    zero in every year to 2040, and from any year of Table 1.13 from its
    second (the index's first) the index's growth carries that year's level
    to every later year's in the table, to the penny."""
    p = system.parameters
    first = min(d.year for d in GROWTH["national_living_wage"]["values"])
    assert first == min(OBR_NATIONAL_LIVING_WAGE) + 1
    for year in range(first, LAST_CHECKED + 1):
        assert _index(p, year) > 0, year
    for base in range(first, max(OBR_NATIONAL_LIVING_WAGE) + 1):
        for year in range(base, max(OBR_NATIONAL_LIVING_WAGE) + 1):
            carried = OBR_NATIONAL_LIVING_WAGE[base] * _index(p, year) / _index(p, base)
            assert round(carried, 2) == pytest.approx(
                round(OBR_NATIONAL_LIVING_WAGE[year], 2), abs=1e-9
            ), (base, year)


def test_after_the_efo_the_series_is_average_earnings_growth():
    """The Low Pay Commission's reference point is two-thirds of median hourly
    earnings (remit 2026), so after the OBR's last estimate the series takes
    average_earnings' growth, year for year, to the end of both series."""
    last = max(OBR_NATIONAL_LIVING_WAGE)
    wage = {d.year for d in GROWTH["national_living_wage"]["values"] if d.year > last}
    earnings = {d.year for d in GROWTH["average_earnings"]["values"] if d.year > last}
    assert wage == earnings
    for year in sorted(wage):
        assert _growth("national_living_wage", year) == _growth(
            "average_earnings", year
        ), year


def test_a_rate_set_later_takes_precedence_and_the_projection_continues():
    """Invariant 4: a national living wage of £14.00 from 1 April 2028, added
    as a rate set by an S.I. would be, holds in 2028-29, and later years are
    £14.00 times the index's growth since. The Carer's Allowance earnings
    limit follows it: 16 x £14.00 = £224, above the projection's own limit."""
    tree = statutory_parameters()
    scale = tree.gov.hmrc.minimum_wage.non_apprentice
    for bracket in scale.brackets[2:]:
        amount = bracket.amount
        amount.values_list.append(
            ParameterAtInstant(amount.name, "2028-04-01", data=14.00)
        )
        amount.values_list.sort(key=lambda entry: entry.instant_str, reverse=True)
    tree, _ = process_parameter_tree(tree)

    def wage(year):
        return tree(f"{year}-01-01").gov.hmrc.minimum_wage.non_apprentice

    assert wage(2027).amounts[-1] == pytest.approx(13.21, abs=1e-9)
    assert wage(2028).amounts[-1] == pytest.approx(14.00, abs=1e-9)
    for year in range(2029, 2032):
        assert wage(year).amounts[-1] == pytest.approx(
            _projected(14.00, tree, 2028, year), abs=1e-9
        ), year
    # Adding a national living wage rate leaves the younger bands' projection
    # unchanged.
    assert wage(2028).amounts[0] == pytest.approx(
        system.parameters("2028-01-01").gov.hmrc.minimum_wage.non_apprentice.amounts[0]
    )

    def limit(year):
        return tree(f"{year}-01-01").gov.dwp.carers_allowance.earnings_limit

    assert limit(2027) == 212
    assert limit(2028) == 224
    assert system.parameters("2028-01-01").gov.dwp.carers_allowance.earnings_limit < 224


def _round_up_to_50p(amount):
    return math.ceil(Fraction(str(amount)) * 2) / 2


# One person in each age band, the national living wage's first.
AGES = {"adult": 30, "aged_23": 23, "aged_21": 21, "aged_19": 19, "aged_16": 16}
BANDS = {"adult": 4, "aged_23": 3, "aged_21": 2, "aged_19": 1, "aged_16": 0}


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_rules_that_read_the_national_living_wage_follow_its_projection():
    """Invariant 5, in the year of the last rate set (April 2027, announced)
    and every projected year to 2040."""
    years = list(range(LAST_YEAR, LAST_CHECKED + 1))
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
    £13.50 x 1.023. £13.50 from 6 April 2027 onwards documents the disclosed
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
