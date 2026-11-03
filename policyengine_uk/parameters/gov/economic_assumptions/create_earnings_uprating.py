"""Build April earnings uprating from the previous May-July AWE growth.

Social Security Administration Act 1992 s150A(2) requires the Pension Credit
standard minimum guarantee to rise at least as much as earnings. This
projection holds amounts unchanged when earnings do not rise. Unlike the
State Pension triple lock, that minimum has no CPI or 2.5% component.

``gov.economic_assumptions.yoy_growth.earnings_uprating`` holds each April's
rise, keyed to 1 January as the other growth series are. It reads the same
completed ``statutory_uprating_inputs.awe_total_pay_may_july`` series as the
triple lock and rounds to the 0.1 percentage points published by the ONS.

``create_economic_assumption_indices`` compounds it into
``gov.economic_assumptions.indices.earnings_uprating``. The yearly series
starts from a 2010 base and runs to one year past the statutory inputs; the
index, like the others built there, ends with the growth series. Published
benefit amounts remain explicit; the index projects later years.
"""

from typing import Dict, Iterable

from policyengine_core.parameters import Parameter, ParameterNode

from policyengine_uk.parameters.gov.economic_assumptions.create_statutory_uprating_inputs import (
    AWE_OBSERVATION_MONTH_DAY,
    last_input_year,
    round_to_published_precision,
)

# The index starts at 1 in this year; its value holds no rise.
BASE_YEAR = 2010
FIRST_UPRATING_YEAR = BASE_YEAR + 1


def earnings_uprating_rate(earnings_growth: float) -> float:
    """April rise at the published earnings rate, without a cut."""
    rate = round_to_published_precision(earnings_growth)
    return rate if rate > 0 else 0.0


def uprating_years(parameters: ParameterNode) -> Iterable[int]:
    """Aprils covered: from April 2011 to one year past the statutory inputs."""
    return range(FIRST_UPRATING_YEAR, last_input_year(parameters) + 2)


def earnings_uprating_rates(parameters: ParameterNode) -> Dict[int, float]:
    """The rise taking effect in April of each year, in year order."""
    earnings = parameters.gov.economic_assumptions.statutory_uprating_inputs.awe_total_pay_may_july
    rates = {}
    for year in uprating_years(parameters):
        may_july = earnings(f"{year - 1}-{AWE_OBSERVATION_MONTH_DAY}")
        if may_july is None:
            raise ValueError(
                f"Missing May-July {year - 1} earnings for the April {year} uprating."
            )
        rates[year] = earnings_uprating_rate(may_july)
    return rates


def add_earnings_uprating(parameters: ParameterNode) -> ParameterNode:
    """Add ``gov.economic_assumptions.yoy_growth.earnings_uprating``."""
    values = {f"{BASE_YEAR}-01-01": None}
    values.update(
        {
            f"{year}-01-01": rate
            for year, rate in earnings_uprating_rates(parameters).items()
        }
    )
    new_parameter = Parameter(
        "gov.economic_assumptions.yoy_growth.earnings_uprating",
        data={
            "description": (
                "Uprating taking effect in April of each year: May-July "
                "earnings growth of the previous year, and no rise when "
                "earnings fall."
            ),
            "values": values,
            "metadata": {
                "unit": "/1",
                "label": "Earnings uprating rate",
                "reference": [
                    {
                        "title": (
                            "Social Security Administration Act 1992, section 150A(2)"
                        ),
                        "href": "https://www.legislation.gov.uk/ukpga/1992/5/section/150A",
                    }
                ],
            },
        },
    )
    parameters.gov.economic_assumptions.yoy_growth.add_child(
        "earnings_uprating", new_parameter
    )
    return parameters
