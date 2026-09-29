"""Build the April uprating by the previous September's CPI.

Social Security Administration Act 1992 s150(1) requires an annual review of
benefit rates "in relation to the general level of prices obtaining in Great
Britain estimated in such manner as the Secretary of State thinks fit".
Where prices have risen, s150(2)(a) requires the non-means-tested sums in
s150(3) (Carer's Allowance, Attendance Allowance, DLA and others) to rise by
at least that percentage, and s150(2)(b) and (7) let the other sums
(Universal Credit and income-related benefit amounts) rise too. Each review
measures prices by the CPI 12-month rate for the September before the April
in which the rates change: September 2025's 3.8% set most April 2026 rates
(written statement HCWS1101, 26 November 2025). Income Tax Act 2007 ss21 and
57 index the basic rate limit and the personal allowance by the same measure
once no freeze applies, and the Universal Credit Act 2025 s1 builds the
2026-27 to 2029-30 standard allowance on it. Past departures (the 1% rises
under the Welfare Benefits Up-rating Act 2013 and the freeze under the
Welfare Reform and Work Act 2016 s11) are in the published rates, not here.

``gov.economic_assumptions.yoy_growth.september_cpi_uprating`` holds the rise
taking effect in April of each year, keyed to 1 January as the other growth
series are. It is September CPI of the previous year from
``statutory_uprating_inputs.cpi_september``, rounded to the 0.1 percentage
points the ONS publishes, as the State Pension triple lock reads it. When
prices fall the rise is zero: s150(2) and ITA 2007 ss21 and 57 only raise
amounts, and benefits were held in April 2016 after September 2015's -0.1%.

``create_economic_assumption_indices`` compounds the rises into
``gov.economic_assumptions.indices.september_cpi_uprating``, which
``gov.benefit_uprating_cpi`` follows, so every parameter uprated by
``gov.benefit_uprating_cpi`` rises by September CPI after its last published
value. The series starts from a 2010 base (April 2011 was the first rise on
September CPI) and runs to one year past the statutory inputs, as the triple
lock does.
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
                f"Missing September {year - 1} CPI for the April {year} "
                "benefit uprating."
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
