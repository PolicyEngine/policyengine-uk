"""Index the personal allowance, the basic rate limit and the equivalent NICs
thresholds by September CPI once their freeze ends.

Income tax
----------
Income Tax Act 2007 s57 raises the personal allowance (s35(1)) for a tax year
if the consumer prices index for the September before the start of the year
is higher than it was for the previous September (s57(2)). The allowance for
the previous year is multiplied by the percentage increase, the result is
rounded up to a multiple of £10, and that increase is added to the previous
allowance (s57(3), Steps 1 to 3). s21(1) and (3) raise the basic rate limit by
the same percentage and round the result up to a multiple of £100. Each year
starts from the rounded amount of the year before.

Finance Act 2021 s5, as amended by Finance Act 2023 s5 and Finance Act 2026
s10, sets the basic rate limit at £37,700 and the personal allowance at
£12,570 for 2022-23 to 2030-31 and disapplies ss21 and 57 for those years.
The parameter files hold those years. From the first tax year after a
parameter's last stated value, ``index_personal_allowance`` and
``index_basic_rate_limit`` apply the statutory steps.

A dated reform states its value for the tax years it covers, and those
years count as stated too (each entry it writes carries
``DATED_CHANGE_UNTIL``, its last day; see
``policyengine_uk.utils.dated_reforms``). Every other year after the last
year the files state is indexed from the year before, so a freeze that ends
resumes indexation from the frozen amount, as s57 Step 1 and s21 Step 1 do
("the allowance ... for the previous tax year", "the basic rate limit for
the previous tax year"); the years between two changes are indexed from the
first. Freezes are legislated that way: Finance Act 2021 s5 (and before it
Finance Act 2019 s5) fixes the amount and disapplies the indexation for
named tax years, and leaves s57 and s21 to apply to the frozen amount after
them. The aligned NICs thresholds are aligned again after a change to one
of them alone. An indexed value starts on 1 January unless a reform's change
runs past that date without covering the year's 30 April sample, in which
case it starts the day after the change.

National Insurance
------------------
No statute indexes the NICs thresholds. SSCBA 1992 s5 needs the Class 1
limits and thresholds specified for each tax year, and the Class 4 limits in
SSCBA s15(3) are subject to alteration by order after the Treasury's annual
review under SSAA 1992 s141. Government policy aligns them with income tax:
the primary threshold and lower profits limit with the personal allowance,
and the upper earnings and profits limits with the higher rate threshold (the
personal allowance plus the basic rate limit). HMRC's Budget 2025 note says
they "will remain aligned" for the frozen years to 2030-31. The Explanatory
Memorandum to SI 2026/231 para 5.1 says that after 2030-31 the personal
allowance, higher rate threshold, UEL, UPL, PT and LPL "will be uprated by the
September Consumer Prices Index (CPI)". Para 5.14 says the UEL has been
aligned with the higher rate threshold since April 2009, and para 5.15 that
for 2026-27 it "will remain at a level equivalent to the annual HRT". Nothing
announced says the NICs thresholds will take the income tax round-ups. The
model assumes the alignment continues, which is consistent with that policy:
after its own last stated value each of these NICs thresholds equals its
income tax equivalent for the same year:

- lower profits limit = personal allowance;
- upper profits limit = personal allowance + basic rate limit;
- primary threshold and upper earnings limit = those annual amounts divided
  by 52 and rounded to the penny, the weekly convention the parameter files
  already use (12,570 / 52 = 241.73 and 50,270 / 52 = 966.73).

The secondary threshold is not aligned with an income tax threshold. HMRC's
Autumn Budget 2024 note says that after its freeze it "will be increased in
line with Consumer Prices Index (CPI)". Nothing later says which CPI, how to
round, or what happens when prices fall, so the model assumes it rises by the
same September CPI increase each year, unrounded and never cut.

The percentage increase for the tax year starting in April of year Y is
``gov.economic_assumptions.yoy_growth.september_cpi_uprating`` at year Y:
September CPI of year Y - 1 to the 0.1 percentage points the ONS publishes,
and zero when prices did not rise. Values are written for each tax year up to
the last year of ``gov.economic_assumptions.indices.september_cpi_uprating``,
the horizon over which every other parameter is uprated. Each is keyed to
1 January of the year the tax year starts, as core uprating keys its values,
so the unconverted ``parameters.baseline`` copy reads the same amount for a
year as fiscal-year conversion gives ``parameters.gov``. Stated values,
including a scenario's overrides, keep their own dates, so that copy read at
1 January lags them by a year, as it does every April-dated parameter. These
parameters carry no ``uprating`` metadata, so core uprating does not extend
them.

The values are computed when the parameters are processed. Every reform route
(a reform dict, ``parameter_changes``, ``Reform.from_dict``) writes its changes
onto the parameters before they are processed, as does a simulation modifier
that resets and reprocesses them (as ``no_economic_assumptions`` does), so the
values are rebuilt with the change: a changed CPI forecast moves all seven,
and a change to the personal allowance or basic rate limit after 2030-31 also
moves the aligned NICs thresholds (see ``policyengine_uk.utils.dated_reforms``).
The exceptions edit the processed parameters, so they do not move the others:
``Scenario.apply`` on an already-built simulation, and a reform-dict key naming
a single day or month (other than 1 January on a calendar-year series, such as
a CPI growth rate, which is a dated change and so does move them).
"""

import datetime
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from typing import Callable, Dict

from policyengine_core.parameters import Parameter, ParameterNode
from policyengine_core.parameters.parameter_at_instant import ParameterAtInstant

WEEKS_IN_YEAR = 52
# ITA 2007 s57(3) Step 2 and s21(3) Step 2.
PERSONAL_ALLOWANCE_MULTIPLE = Decimal(10)
BASIC_RATE_LIMIT_MULTIPLE = Decimal(100)
PENNY = Decimal("0.01")
# Fiscal-year conversion reads each tax year's value at 30 April.
FISCAL_YEAR_SAMPLE_MONTH_DAY = "04-30"
# Indexed values are keyed to 1 January, as core uprating keys its values.
INDEXED_VALUE_MONTH_DAY = "01-01"
# Metadata on an entry a dated reform wrote: the last day (YYYY-MM-DD) its
# value is stated for. The tax years whose 30 April sample falls between the
# entry's date and that day are stated, not indexed.
DATED_CHANGE_UNTIL = "dated_change_until"
# Parameter metadata a dated reform writes before it changes the parameter:
# the last tax year the parameter files state. A change can replace the
# files' last value (the 2030-04-06 value that ends a freeze), so the years
# the files state cannot be read from the changed timeline alone. Removed
# once the indexation has run.
FILES_LAST_TAX_YEAR = "files_last_tax_year"
# The parameters this module writes values for after their stated years.
INDEXED_THRESHOLDS = (
    "gov.hmrc.income_tax.allowances.personal_allowance.amount",
    "gov.hmrc.income_tax.rates.uk[1].threshold",
    "gov.hmrc.national_insurance.class_1.thresholds.primary_threshold",
    "gov.hmrc.national_insurance.class_1.thresholds.upper_earnings_limit",
    "gov.hmrc.national_insurance.class_1.thresholds.secondary_threshold",
    "gov.hmrc.national_insurance.class_4.thresholds.lower_profits_limit",
    "gov.hmrc.national_insurance.class_4.thresholds.upper_profits_limit",
)


def to_decimal(value: float) -> Decimal:
    """Exact decimal for a stored amount or rate, without binary noise."""
    return Decimal(repr(float(value)))


def round_up_to_multiple(amount: Decimal, multiple: Decimal) -> Decimal:
    """The amount if it is a multiple, else the next multiple above it."""
    return (amount / multiple).to_integral_value(ROUND_CEILING) * multiple


def index_personal_allowance(previous: Decimal, increase: Decimal) -> Decimal:
    """ITA 2007 s57(2)-(3): the allowance for the next tax year.

    ``increase`` is the September CPI increase as a fraction (0.021 for 2.1%).
    """
    if increase <= 0:
        return previous
    step_1 = previous * increase
    step_2 = round_up_to_multiple(step_1, PERSONAL_ALLOWANCE_MULTIPLE)
    return previous + step_2


def index_basic_rate_limit(previous: Decimal, increase: Decimal) -> Decimal:
    """ITA 2007 s21(1) and (3): the basic rate limit for the next tax year."""
    if increase <= 0:
        return previous
    step_1 = previous * (1 + increase)
    return round_up_to_multiple(step_1, BASIC_RATE_LIMIT_MULTIPLE)


def weekly_equivalent(annual: Decimal) -> Decimal:
    """Annual amount over 52, to the penny, as the parameter files store it."""
    return (annual / WEEKS_IN_YEAR).quantize(PENNY, ROUND_HALF_UP)


def index_secondary_threshold(previous: Decimal, increase: Decimal) -> Decimal:
    """The secondary threshold rises with CPI, unrounded, and never falls."""
    if increase <= 0:
        return previous
    return previous * (1 + increase)


def first_tax_year(instant_str: str) -> int:
    """First tax year (by its starting calendar year) a dated value covers."""
    year = int(instant_str[:4])
    return year if instant_str[5:] <= FISCAL_YEAR_SAMPLE_MONTH_DAY else year + 1


def is_dated_change(value: ParameterAtInstant) -> bool:
    return DATED_CHANGE_UNTIL in (value.metadata or {})


def last_stated_tax_year(parameter: Parameter) -> int:
    """Tax year of the parameter's latest value in its files.

    Values a dated reform wrote are left out; ``dated_change_tax_years``
    gives the years they state. Where a reform replaced the files' last value,
    the year it recorded (``FILES_LAST_TAX_YEAR``) counts.
    """
    stated = [
        first_tax_year(value.instant_str)
        for value in parameter.values_list
        if not is_dated_change(value)
    ]
    recorded = (parameter.metadata or {}).get(FILES_LAST_TAX_YEAR)
    if recorded is not None:
        stated.append(int(recorded))
    # values_list is latest first.
    return max(stated or [first_tax_year(parameter.values_list[0].instant_str)])


def dated_change_tax_years(parameter: Parameter) -> set:
    """Tax years whose 30 April falls within a dated reform's change."""
    years = set()
    for value in parameter.values_list:
        if not is_dated_change(value):
            continue
        until = value.metadata[DATED_CHANGE_UNTIL]
        year = first_tax_year(value.instant_str)
        # Zero-padded, as instant strings are: an ETERNITY change starts in
        # year 1.
        while f"{year:04d}-{FISCAL_YEAR_SAMPLE_MONTH_DAY}" <= until:
            years.add(year)
            year += 1
    return years


def stated_tax_year(parameter: Parameter) -> Callable[[int], bool]:
    """Whether a tax year's value is stated (in the files or by a reform)."""
    last_stated = last_stated_tax_year(parameter)
    changed = dated_change_tax_years(parameter)
    return lambda year: year <= last_stated or year in changed


def value_in_tax_year(parameter: Parameter, year: int) -> Decimal:
    return to_decimal(parameter(f"{year}-{FISCAL_YEAR_SAMPLE_MONTH_DAY}"))


def tax_year_path(
    parameter: Parameter,
    years: range,
    increases: Dict[int, Decimal],
    step: Callable[[Decimal, Decimal], Decimal],
) -> Dict[int, Decimal]:
    """The parameter's value in each tax year in ``years``, stated or indexed.

    Stated years read the parameter; each other year applies ``step`` to the
    year before with that year's increase. ``years`` starts at a stated year.
    """
    stated = stated_tax_year(parameter)
    values = {}
    for year in years:
        if stated(year):
            values[year] = value_in_tax_year(parameter, year)
        else:
            values[year] = step(values[year - 1], increases[year])
    return values


def unstated_value_date(parameter: Parameter, year: int) -> str:
    """Where a tax year's indexed value starts.

    1 January, as core uprating keys its values, unless a dated reform's
    change runs from before that tax year's 30 April sample to after
    1 January without covering it: the value then starts the day after the
    change, so the change cannot reach a tax year it does not cover.
    """
    start = f"{year}-{INDEXED_VALUE_MONTH_DAY}"
    sample = f"{year}-{FISCAL_YEAR_SAMPLE_MONTH_DAY}"
    for value in parameter.values_list:
        until = (value.metadata or {}).get(DATED_CHANGE_UNTIL)
        if until is None or value.instant_str > sample or until >= sample:
            continue
        if until >= start:
            next_day = datetime.date.fromisoformat(until) + datetime.timedelta(days=1)
            start = max(start, next_day.isoformat())
    return start


def write_unstated_tax_years(parameter: Parameter, values: Dict[int, Decimal]) -> None:
    """Add a value for each tax year neither the files nor a reform state."""
    stated = stated_tax_year(parameter)
    for year, value in sorted(values.items()):
        if not stated(year):
            parameter.values_list.append(
                ParameterAtInstant(
                    parameter.name,
                    unstated_value_date(parameter, year),
                    data=float(value),
                )
            )
    parameter.values_list.sort(key=lambda value: value.instant_str, reverse=True)


def september_cpi_increases(parameters: ParameterNode) -> Dict[int, Decimal]:
    """The September CPI increase for each tax year to the uprating horizon."""
    economic_assumptions = parameters.gov.economic_assumptions
    rises = economic_assumptions.yoy_growth.september_cpi_uprating
    index = economic_assumptions.indices.september_cpi_uprating
    years = [int(value.instant_str[:4]) for value in index.values_list]
    # The index's first year is its base, with no increase.
    return {
        year: to_decimal(rises(f"{year}-01-01"))
        for year in range(min(years) + 1, max(years) + 1)
    }


def add_threshold_indexation(parameters: ParameterNode) -> ParameterNode:
    """Index the income tax and NICs thresholds after their last stated values.

    Runs after ``create_economic_assumption_indices``, which builds the
    September CPI index whose horizon this follows.
    """
    increases = september_cpi_increases(parameters)
    income_tax = parameters.gov.hmrc.income_tax
    class_1 = parameters.gov.hmrc.national_insurance.class_1.thresholds
    class_4 = parameters.gov.hmrc.national_insurance.class_4.thresholds
    personal_allowance_parameter = income_tax.allowances.personal_allowance.amount
    basic_rate_limit_parameter = income_tax.rates.uk.brackets[1].threshold
    indexed = [
        personal_allowance_parameter,
        basic_rate_limit_parameter,
        class_1.primary_threshold,
        class_1.upper_earnings_limit,
        class_1.secondary_threshold,
        class_4.lower_profits_limit,
        class_4.upper_profits_limit,
    ]
    # From the earliest last value in the files, so the income tax amounts
    # cover every year a NICs threshold takes from them.
    years = range(
        min(last_stated_tax_year(parameter) for parameter in indexed),
        max(increases) + 1,
    )

    personal_allowance = tax_year_path(
        personal_allowance_parameter, years, increases, index_personal_allowance
    )
    basic_rate_limit = tax_year_path(
        basic_rate_limit_parameter, years, increases, index_basic_rate_limit
    )
    higher_rate_threshold = {
        year: personal_allowance[year] + basic_rate_limit[year] for year in years
    }
    secondary_threshold = tax_year_path(
        class_1.secondary_threshold, years, increases, index_secondary_threshold
    )

    write_unstated_tax_years(personal_allowance_parameter, personal_allowance)
    write_unstated_tax_years(basic_rate_limit_parameter, basic_rate_limit)
    write_unstated_tax_years(class_4.lower_profits_limit, personal_allowance)
    write_unstated_tax_years(class_4.upper_profits_limit, higher_rate_threshold)
    write_unstated_tax_years(
        class_1.primary_threshold,
        {year: weekly_equivalent(value) for year, value in personal_allowance.items()},
    )
    write_unstated_tax_years(
        class_1.upper_earnings_limit,
        {
            year: weekly_equivalent(value)
            for year, value in higher_rate_threshold.items()
        },
    )
    write_unstated_tax_years(class_1.secondary_threshold, secondary_threshold)
    for parameter in indexed:
        (parameter.metadata or {}).pop(FILES_LAST_TAX_YEAR, None)
    return parameters
