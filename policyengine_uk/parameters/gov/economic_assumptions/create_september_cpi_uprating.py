"""Build the April uprating by the previous September's CPI.

Income Tax Act 2007 ss21 and 57 index the basic rate limit and the personal
allowance for a tax year by the percentage increase in the consumer prices
index for the September before it, and only when prices rose (ss21(1) and
57(2)). The Explanatory Memorandum to SI 2026/231 (paras 5.1 and 5.2) says the
equivalent NICs thresholds will be uprated by September CPI once their freeze
ends, and that the Class 2 and Class 3 rates, the lower earnings limit and the
small profits threshold were raised for 2026-27 by September 2025's 3.8%.

``gov.economic_assumptions.yoy_growth.september_cpi_uprating`` holds the rise
taking effect in April of each year, keyed to 1 January as the other growth
series are. It is September CPI of the previous year from
``statutory_uprating_inputs.cpi_september``, rounded to the 0.1 percentage
points the ONS publishes, as the State Pension triple lock reads it. When
prices fall the rise is zero, as ss21 and 57 only raise amounts.

``create_economic_assumption_indices`` compounds the rises into
``gov.economic_assumptions.indices.september_cpi_uprating``.
``policyengine_uk.parameters.gov.hmrc.create_threshold_indexation`` uses the
rises, up to the index's last year, to index the income tax and NICs
thresholds after their freeze. The series starts from a 2010 base, the year
of the first September CPI input, and runs to one year past the statutory
inputs, as the triple lock does.
"""

from typing import Dict, Iterable

from policyengine_core.parameters import Parameter, ParameterNode

from policyengine_uk.parameters.gov.economic_assumptions.create_statutory_uprating_inputs import (
    CPI_OBSERVATION_MONTH_DAY,
    last_input_year,
    round_to_published_precision,
)

# The index starts at 1 in this year; its value holds no rise.
BASE_YEAR = 2010
FIRST_UPRATING_YEAR = BASE_YEAR + 1


def september_cpi_uprating_rate(september_cpi: float) -> float:
    """April rise for a September CPI rate: the published rate, never a cut."""
    rate = round_to_published_precision(september_cpi)
    # Not max(rate, 0.0), which keeps a rounded -0.0.
    return rate if rate > 0 else 0.0


def uprating_years(parameters: ParameterNode) -> Iterable[int]:
    """Aprils covered: from April 2011 to one year past the statutory inputs."""
    return range(FIRST_UPRATING_YEAR, last_input_year(parameters) + 2)


def september_cpi_uprating_rates(parameters: ParameterNode) -> Dict[int, float]:
    """The rise taking effect in April of each year, in year order."""
    cpi_september = (
        parameters.gov.economic_assumptions.statutory_uprating_inputs.cpi_september
    )
    rates = {}
    for year in uprating_years(parameters):
        september = cpi_september(f"{year - 1}-{CPI_OBSERVATION_MONTH_DAY}")
        if september is None:
            raise ValueError(
                f"Missing September {year - 1} CPI for the April {year} uprating."
            )
        rates[year] = september_cpi_uprating_rate(september)
    return rates


def add_september_cpi_uprating(parameters: ParameterNode) -> ParameterNode:
    """Add ``gov.economic_assumptions.yoy_growth.september_cpi_uprating``."""
    values = {f"{BASE_YEAR}-01-01": None}
    values.update(
        {
            f"{year}-01-01": rate
            for year, rate in september_cpi_uprating_rates(parameters).items()
        }
    )
    new_parameter = Parameter(
        "gov.economic_assumptions.yoy_growth.september_cpi_uprating",
        data={
            "description": (
                "Uprating taking effect in April of each year: September "
                "CPI inflation of the previous year, and no rise when prices "
                "fall."
            ),
            "values": values,
            "metadata": {
                "unit": "/1",
                "label": "September CPI uprating rate",
            },
        },
    )
    parameters.gov.economic_assumptions.yoy_growth.add_child(
        "september_cpi_uprating", new_parameter
    )
    return parameters
