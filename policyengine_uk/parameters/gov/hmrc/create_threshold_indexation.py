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

National Insurance
------------------
No statute indexes the NICs thresholds. SSCBA 1992 s5 needs the Class 1
limits and thresholds specified for each tax year, and the Class 4 limits in
SSCBA s15(3) are subject to alteration by order after the Treasury's annual
review under SSAA 1992 s141. Government policy keeps them aligned with income
tax: the primary threshold and lower profits limit with the personal
allowance, and the upper earnings and profits limits with the higher rate
threshold (the personal allowance plus the basic rate limit). HMRC's Budget
2025 note says they "will remain aligned" through 2030-31, and the
Explanatory Memorandum to SI 2026/231 (paras 5.1 and 5.15) says all six
thresholds will then be "uprated by the September Consumer Prices Index" and
that the UEL stays "equivalent to the annual HRT". So after its own last
stated value each of these NICs thresholds equals its income tax equivalent
for the same year:

- lower profits limit = personal allowance;
- upper profits limit = personal allowance + basic rate limit;
- primary threshold and upper earnings limit = those annual amounts divided
  by 52 and rounded to the penny, the weekly convention the parameter files
  already use (12,570 / 52 = 241.73 and 50,270 / 52 = 966.73).

The secondary threshold is not aligned with an income tax threshold. HMRC's
Autumn Budget 2024 note says that after its freeze it "will be increased in
line with Consumer Prices Index (CPI)". Nothing later sets a rounding rule, so
it rises by the same September CPI increase each year, unrounded.

The percentage increase for the tax year starting in April of year Y is
``gov.economic_assumptions.yoy_growth.september_cpi_uprating`` at year Y:
September CPI of year Y - 1 to the 0.1 percentage points the ONS publishes,
and zero when prices did not rise. Values are written for each tax year up to
the last year of ``gov.economic_assumptions.indices.september_cpi_uprating``,
the horizon over which every other parameter is uprated. These parameters
carry no ``uprating`` metadata, so core uprating does not extend them.

A reform that changes one of these parameters after the tax-benefit system is
built does not move the others. A scenario applied before data load (for
example one that changes the CPI forecast) reprocesses the parameters, so the
thresholds follow it.
"""

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
# Tax years start on 6 April.
TAX_YEAR_START_MONTH_DAY = "04-06"


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


def last_stated_tax_year(parameter: Parameter) -> int:
    """Tax year of the parameter's latest dated value."""
    return max(first_tax_year(value.instant_str) for value in parameter.values_list)


def value_in_tax_year(parameter: Parameter, year: int) -> Decimal:
    return to_decimal(parameter(f"{year}-{FISCAL_YEAR_SAMPLE_MONTH_DAY}"))


def tax_year_path(
    parameter: Parameter,
    years: range,
    increases: Dict[int, Decimal],
    step: Callable[[Decimal, Decimal], Decimal],
) -> Dict[int, Decimal]:
    """The parameter's value in each tax year in ``years``, stated or indexed.

    Years up to the last stated value read the parameter; each later year
    applies ``step`` to the year before with that year's increase.
    """
    last_stated = last_stated_tax_year(parameter)
    values = {}
    for year in years:
        if year <= last_stated:
            values[year] = value_in_tax_year(parameter, year)
        else:
            values[year] = step(values[year - 1], increases[year])
    return values


def write_after_last_stated_value(
    parameter: Parameter, values: Dict[int, Decimal]
) -> None:
    """Add a value from 6 April of each year after the last stated one."""
    last_stated = last_stated_tax_year(parameter)
    for year, value in sorted(values.items()):
        if year > last_stated:
            parameter.values_list.append(
                ParameterAtInstant(
                    parameter.name,
                    f"{year}-{TAX_YEAR_START_MONTH_DAY}",
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
    # From the earliest last stated value, so the income tax amounts cover
    # every year a NICs threshold takes from them.
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

    write_after_last_stated_value(personal_allowance_parameter, personal_allowance)
    write_after_last_stated_value(basic_rate_limit_parameter, basic_rate_limit)
    write_after_last_stated_value(class_4.lower_profits_limit, personal_allowance)
    write_after_last_stated_value(class_4.upper_profits_limit, higher_rate_threshold)
    write_after_last_stated_value(
        class_1.primary_threshold,
        {year: weekly_equivalent(value) for year, value in personal_allowance.items()},
    )
    write_after_last_stated_value(
        class_1.upper_earnings_limit,
        {
            year: weekly_equivalent(value)
            for year, value in higher_rate_threshold.items()
        },
    )
    write_after_last_stated_value(class_1.secondary_threshold, secondary_threshold)
    return parameters
