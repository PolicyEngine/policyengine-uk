"""Local Housing Allowance determinations.

Rent officers determine LHA rates each January for every Broad Rental Market
Area (BRMA) and category of dwelling, and the rates take effect the following
April: the Valuation Office Agency in England, Rent Officers Wales, Rent Service
Scotland, and the Northern Ireland Housing Executive. The model reads the
published determinations from ``lha_published_rates.csv.gz`` and re-applies the
rules of Schedule 3B to the Rent Officers (Housing Benefit Functions) Order
1997, and Schedule 1 to the Rent Officers (Universal Credit Functions) Order
2013, so that freeze, percentile and maximum reforms move rates the way a
determination would:

1. the rent at the 30th percentile of the BRMA's list of rents for the twelve
   months to the previous September (Sch 3B para 2(4) to (8));
2. the lower of that rent and the national maximum (para 2(2));
3. the anomalous-rate rule: a category is raised to the highest rate of any
   smaller category (para 3);
4. from April 2024, the minimum: no rate below the one determined on 31 March
   2020 (para 3A, inserted by SI 2024/11);
5. rounded to the nearest penny, halves up (para 2(10)).

While ``gov.dwp.LHA.freeze`` is true, the rates are those of the last year in
which it was false (the Modification Orders substitute the earlier
determination for para 2(2)).

Determinations before April 2020 followed rules this model does not encode
(CPI and 1% uprating to 2015, the 2016-2020 freeze with targeted affordability
uplifts), so for those years the published rate itself is the determination.
"""

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

CATEGORIES = ("A", "B", "C", "D", "E")

# The first determination the model recomputes from its rules rather than
# reading as published: the April 2020 reset to the 30th percentile.
FIRST_RULES_YEAR = 2020

# The percentile the published percentile rents are taken at.
PUBLISHED_PERCENTILE = 0.3

# Determinations that reset rates to the 30th percentile, and the published
# tables that held them in cash terms, under the Social Security (Coronavirus)
# (Further Measures) Regulations 2020 reg 4, the Rent Officers (Housing Benefit
# and Universal Credit Functions) (Amendment) Order 2024, the Modification
# Orders SI 2020/1519, 2021/1380, 2023/6, 2025/5 and 2026/5, and their Northern
# Ireland equivalents.
RESET_YEARS = (2020, 2024)
HELD_TABLES = {2021: 2020, 2022: 2020, 2023: 2020, 2025: 2024, 2026: 2024}

# The UC Order converts a rent to a monthly one through the rent for a year,
# divided by 12 (Sch 1 para 3(8)); Sch 3B para 2(5)(c) converts the other way,
# through the rent for a year divided by 365 and multiplied by 7. A weekly
# rent's year is therefore 365/7 weeks. DWP's published monthly rates for the
# April 2020 and April 2024 determinations in England are the weekly 30th
# percentile times this factor, to within 3p, which is the rounding of the
# weekly figure. The model uses the factor only where no monthly rate is
# published.
WEEKLY_TO_MONTHLY = 365 / 7 / 12

LHA_DIRECTORY = (
    Path(__file__).resolve().parents[1] / "parameters" / "gov" / "dwp" / "LHA"
)
PUBLISHED_RATES_PATH = LHA_DIRECTORY / "lha_published_rates.csv.gz"
LIST_OF_RENTS_PATH = LHA_DIRECTORY / "lha_list_of_rents.csv.gz"

MEASURES = ("rate", "percentile_30", "uc_rate", "uc_percentile_30")


def round_half_up(values: np.ndarray) -> np.ndarray:
    """Round pounds to the nearest penny, halves up (Sch 3B para 2(10)).

    np.round is half-even. Pence are snapped to 6dp first, because an exact
    half such as 298.835 is held as 29883.499999999996 once scaled.
    """
    values = np.asarray(values, dtype=float)
    return np.floor(np.round(values * 100, 6) + 0.5) / 100


class PublishedRates:
    """The published LHA tables as [year, BRMA, category] arrays."""

    def __init__(self, table: pd.DataFrame):
        self.years = np.array(sorted(table.year.unique()), dtype=int)
        self.brmas = pd.Index(sorted(table.brma.unique()))
        shape = (len(self.years), len(self.brmas), len(CATEGORIES))
        year_index = np.searchsorted(self.years, table.year.to_numpy())
        brma_index = self.brmas.get_indexer(table.brma)
        category_index = pd.Index(CATEGORIES).get_indexer(table.lha_category)
        if (category_index < 0).any():
            raise ValueError("Unknown LHA category in the published rates")
        for measure in MEASURES:
            values = np.full(shape, np.nan)
            values[year_index, brma_index, category_index] = table[measure].to_numpy(
                dtype=float
            )
            setattr(self, measure, values)

    def latest(self, measure: str, year: int) -> tuple[np.ndarray, np.ndarray]:
        """The latest published value at or before ``year`` for each cell.

        Returns the values and the year each was published for, as
        [BRMA, category] arrays. Where nothing is published by ``year``, the
        earliest published value is used and its year returned.
        """
        values = getattr(self, measure)
        available = ~np.isnan(values)
        eligible = available & (self.years <= year)[:, None, None]
        reversed_positions = np.argmax(eligible[::-1], axis=0)
        latest = len(self.years) - 1 - reversed_positions
        earliest = np.argmax(available, axis=0)
        position = np.where(eligible.any(axis=0), latest, earliest)
        chosen = np.take_along_axis(values, position[None], axis=0)[0]
        return chosen, self.years[position]

    def at(self, measure: str, year: int) -> np.ndarray:
        """Values published for exactly ``year`` (NaN where none)."""
        values = getattr(self, measure)
        matches = np.flatnonzero(self.years == year)
        if len(matches) == 0:
            return np.full(values.shape[1:], np.nan)
        return values[matches[0]]


@lru_cache(maxsize=1)
def published_rates() -> PublishedRates:
    return PublishedRates(pd.read_csv(PUBLISHED_RATES_PATH))


@lru_cache(maxsize=1)
def _sorted_list_of_rents() -> dict:
    """The latest list of rents, sorted, keyed by (BRMA, category)."""
    rents = pd.read_csv(LIST_OF_RENTS_PATH)
    rents = rents[rents.year == rents.year.max()]
    return {
        key: np.sort(group.weekly_rent.to_numpy(dtype=float))
        for key, group in rents.groupby(["brma", "lha_category"])
    }


def statutory_percentile(rents: np.ndarray, percentile: float) -> float:
    """The rent at ``percentile`` of an ascending list (Sch 3B para 2(8)).

    Where the list length times the percentile is a whole number P, the rent
    is the mean of the rents at positions P and P + 1; otherwise it is the
    rent at that product rounded up. Positions count from one.
    """
    count = len(rents)
    position = count * percentile
    whole = round(position)
    if abs(position - whole) < 1e-9 and 1 <= whole < count:
        return (rents[whole - 1] + rents[whole]) / 2
    index = min(max(int(np.ceil(position - 1e-9)), 1), count)
    return rents[index - 1]


@lru_cache(maxsize=16)
def _percentile_ratios(percentile: float) -> np.ndarray:
    """Rent at ``percentile`` relative to the 30th, per BRMA and category.

    The published tables give only the 30th percentile, so another percentile
    is reached by scaling it by this ratio from the model's list of rents.
    Cells the list does not cover keep a ratio of one.
    """
    rates = published_rates()
    ratios = np.ones((len(rates.brmas), len(CATEGORIES)))
    for (brma, category), rents in _sorted_list_of_rents().items():
        position = rates.brmas.get_indexer([brma])[0]
        if position < 0 or category not in CATEGORIES:
            continue
        base = statutory_percentile(rents, PUBLISHED_PERCENTILE)
        if base > 0:
            ratios[position, CATEGORIES.index(category)] = (
                statutory_percentile(rents, percentile) / base
            )
    return ratios


def find_freeze_anchor(freeze_parameter, period: str) -> str:
    """Finds the instant whose rates a frozen LHA rate is held at.

    Frozen rates are held in cash terms at the level set in the most recent
    year in which LHA was *not* frozen, so this returns the start instant of
    the latest unfrozen period before the given period.

    Args:
        freeze_parameter (Parameter): The LHA freeze parameter.
        period (str): The period to search up to.

    Returns:
        str: The instant of the latest unfrozen period, or None if not frozen.
    """
    # Values at or before the requested period, newest first.
    relevant_values = [
        v for v in freeze_parameter.values_list if v.instant_str <= str(period)
    ]

    if not relevant_values:
        return None

    if not relevant_values[0].value:
        # Not currently frozen.
        return None

    # Walk back to the most recent value that is False; the rates in force
    # during the freeze are the ones determined in that year.
    for value in relevant_values:
        if not value.value:
            return value.instant_str

    # Frozen for the whole of the parameter's history; fall back to the
    # oldest value available.
    return relevant_values[-1].instant_str


def determination_year(lha, year: int) -> int:
    """The year whose determination is in force in ``year``.

    A year is a UK fiscal year: parameters are read at 30 April, so ``year``
    2025 is April 2025 to March 2026 and takes the determination made in
    January 2025, or the one it is frozen at.
    """
    if lha.freeze(str(year)):
        return int(find_freeze_anchor(lha.freeze, f"{year}-01-01")[:4])
    return int(year)


def restatement(measure: str, determined: int, year: int) -> np.ndarray:
    """How later held tables restate the rates determined in ``determined``.

    A table that holds an earlier determination should repeat its rates, and
    in England it always does. Rent Officers Wales's tables for April 2022 and
    April 2023, which say the rates are fixed at the April 2020 rate, give
    different figures from its April 2020 and April 2021 tables for some
    cells, and DWP's monthly tables follow them. The model takes each table
    as published: this returns the change from the determination to the latest
    held table by ``year`` (zero almost everywhere), which is added to the
    held determination whatever reform it is under.
    """
    rates = published_rates()
    original = rates.at(measure, determined)
    change = np.zeros(original.shape)
    for table_year in sorted(HELD_TABLES):
        if HELD_TABLES[table_year] == determined and table_year <= year:
            held = rates.at(measure, table_year)
            known = ~np.isnan(held) & ~np.isnan(original)
            change[known] = (held - original)[known]
    return change


def determination(parameters, determined: int, universal_credit: bool = False):
    """The rates determined in ``determined`` for every BRMA and category.

    Returns (percentile, rate) as [BRMA, category] arrays, weekly for Housing
    Benefit and monthly for Universal Credit.
    """
    lha = parameters.gov.dwp.LHA
    rates = published_rates()
    measure = "uc_rate" if universal_credit else "rate"

    if determined < FIRST_RULES_YEAR:
        rate, _ = rates.latest("rate", determined)
        percentile, _ = rates.latest("percentile_30", determined)
        if universal_credit:
            uc_rate, uc_year = rates.latest("uc_rate", determined)
            published_by_then = uc_year <= determined
            # Where no monthly rate was published (Northern Ireland), convert
            # the weekly rate as the determinations from April 2020 do.
            rate = np.where(
                published_by_then & ~np.isnan(uc_rate),
                uc_rate,
                round_half_up(rate * WEEKLY_TO_MONTHLY),
            )
            percentile = round_half_up(percentile * WEEKLY_TO_MONTHLY)
        percentile = np.where(np.isnan(percentile), rate, percentile)
        return percentile, rate

    weekly, base_year = rates.latest("percentile_30", determined)
    if universal_credit:
        published_monthly = np.full(weekly.shape, np.nan)
        for value in np.unique(base_year):
            in_year = base_year == value
            published_monthly[in_year] = rates.at("uc_percentile_30", value)[in_year]
        percentile = np.where(
            np.isnan(published_monthly), weekly * WEEKLY_TO_MONTHLY, published_monthly
        )
    else:
        percentile = weekly

    # Rents grow from the year the latest percentile was published to the
    # determination year.
    index = parameters.gov.indices.private_rent_index
    growth = np.ones(weekly.shape)
    for value in np.unique(base_year[~np.isnan(weekly)]):
        if value < determined:
            growth[base_year == value] = index(str(determined)) / index(str(value))
    percentile = percentile * growth

    share = lha.percentile(str(determined))
    if abs(share - PUBLISHED_PERCENTILE) > 1e-9:
        percentile = percentile * _percentile_ratios(float(share))
    percentile = round_half_up(percentile)

    maxima = lha.maximum_monthly if universal_credit else lha.maximum
    cap = np.array(
        [maxima.children[category](str(determined)) for category in CATEGORIES]
    )
    rate = np.minimum(percentile, cap[None, :])
    # Sch 3B para 3: no category below a smaller one.
    rate = np.maximum.accumulate(rate, axis=1)
    if lha.march_2020_minimum(str(determined)):
        # Sch 3B para 3A: no rate below the one determined on 31 March 2020,
        # as the latest held table states it.
        minimum = rates.at(measure, FIRST_RULES_YEAR) + restatement(
            measure, FIRST_RULES_YEAR, determined
        )
        rate = np.where(np.isnan(minimum), rate, np.maximum(rate, minimum))
    return percentile, rate


def lha_rates(parameters, year: int, universal_credit: bool = False) -> dict:
    """LHA rates in force in ``year`` for every BRMA and category.

    Args:
        parameters: The root parameter node (``tax_benefit_system.parameters``).
        year: The fiscal year the rates apply in.
        universal_credit: Monthly Universal Credit rates (Rent Officers
            (Universal Credit Functions) Order 2013) rather than weekly
            Housing Benefit ones.

    Returns:
        A dict with ``brmas`` (a pandas Index of BRMA names), ``percentile``
        (the rent at the percentile, before the maximum, anomalous-rate and
        minimum rules) and ``rate`` (the LHA in force), both [BRMA, category]
        arrays, weekly for Housing Benefit and monthly for Universal Credit.
    """
    lha = parameters.gov.dwp.LHA
    determined = determination_year(lha, year)
    percentile, rate = determination(parameters, determined, universal_credit)
    if determined != year and determined >= FIRST_RULES_YEAR:
        measure = "uc_rate" if universal_credit else "rate"
        rate = round_half_up(rate + restatement(measure, determined, year))
        rate = np.maximum.accumulate(rate, axis=1)
    return dict(brmas=published_rates().brmas, percentile=percentile, rate=rate)


def benunit_lha(benunit, period, measure: str, universal_credit: bool = False):
    """Look up an LHA measure for each benefit unit's BRMA and category."""
    parameters = benunit.simulation.tax_benefit_system.parameters
    table = lha_rates(parameters, period.start.year, universal_credit)
    brma = benunit.value_from_first_person(
        benunit.members.household("brma", period).decode_to_str()
    )
    category = benunit("LHA_category", period).decode_to_str()
    brma_index = table["brmas"].get_indexer(brma)
    category_index = pd.Index(CATEGORIES).get_indexer(category)
    values = table[measure][np.maximum(brma_index, 0), np.maximum(category_index, 0)]
    return np.where((brma_index < 0) | (category_index < 0), np.nan, values)
