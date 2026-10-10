"""Build the State Pension uprating series from the statutory inputs.

Each April the basic and new State Pension rise by the highest of:

- earnings growth: average weekly earnings, total pay, whole economy, the
  three months May to July of the previous year on a year earlier;
- CPI inflation: the 12-month rate in September of the previous year;
- the minimum rate (2.5%).

The inputs live in ``gov.economic_assumptions.statutory_uprating_inputs``,
which ``create_statutory_uprating_inputs`` completes with forecasts before
this module runs. Each input is rounded to the one decimal place the ONS
publishes, as the uprating review uses the published figure.

With ``active`` false there is no triple lock, only the statutory minimum
from the review under Social Security Administration Act 1992 s150A as it
stands: the pension rises by earnings growth, and not at all when earnings
fall. The one-year modifications of s150A for April 2021 and April 2022 are
not applied, and ``include_earnings``, ``include_inflation`` and
``minimum_rate`` are ignored.

Years with a published rate that the rule cannot reproduce are overridden in
``triple_lock/outturn.yaml``. Only April 2011, when the basic State Pension
rose by RPI during the switch to CPI, needs one; the April 2022 suspension of
the earnings element is expressed through ``include_earnings``.

``earnings_path_guarantee`` adds an optional floor for modelling reforms: in
each year it applies, the pension also rises at least enough to stay on an
earnings path started from its level in the year before the guarantee first
applied. Current law leaves it off.

The output parameter ``gov.economic_assumptions.yoy_growth.triple_lock`` holds
the rate taking effect in April of each year, keyed to 1 January as the other
growth series are, and runs to one year past the last year of the
economic-assumption series.
"""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from typing import Dict, Iterable, Optional

from policyengine_core.parameters import Parameter, ParameterNode

from policyengine_uk.parameters.gov.economic_assumptions.create_statutory_uprating_inputs import (
    AWE_OBSERVATION_MONTH_DAY,
    CPI_OBSERVATION_MONTH_DAY,
    last_input_year,
)

FIRST_UPRATING_YEAR = 2011
# Published statistics are quoted to one decimal place of a percentage.
PUBLISHED_PRECISION = Decimal("0.001")
# Guards the round-up of a guaranteed minimum against floating-point noise,
# so a ratio of 1.025000000000001 is not taken up to 2.6%.
RATIO_PRECISION = Decimal("0.000000001")


def uprating_instant(year: int) -> str:
    """Date at which policy parameters are read for the April ``year`` uprating.

    30 April is the date fiscal-year conversion samples. A YAML value from
    1 January, or a parameter change keyed to the bare year (the fiscal year
    from 6 April) or to ``year:YYYY-01-01:N``, takes effect in the uprating
    for that April. A change keyed to a single day covers only that day.
    """
    return f"{year}-04-30"


def round_to_published_precision(rate: float) -> float:
    """Round a growth rate to 0.1 percentage points, halves away from zero."""
    return float(
        Decimal(repr(float(rate))).quantize(PUBLISHED_PRECISION, ROUND_HALF_UP)
    )


def round_up_to_published_precision(rate: float) -> float:
    """Round a guaranteed minimum rate up to the next 0.1 percentage points."""
    cleaned = Decimal(repr(float(rate))).quantize(RATIO_PRECISION, ROUND_HALF_UP)
    return float(cleaned.quantize(PUBLISHED_PRECISION, ROUND_CEILING))


@dataclass(frozen=True)
class UpratingYear:
    """Inputs to the April uprating in one year."""

    earnings: float
    cpi: float
    minimum_rate: float
    active: bool = True
    include_earnings: bool = True
    include_inflation: bool = True
    earnings_path_guarantee: bool = False
    outturn: Optional[float] = None


def triple_lock_rate(
    earnings: float,
    cpi: float,
    minimum_rate: float,
    include_earnings: bool = True,
    include_inflation: bool = True,
) -> float:
    """The highest of the included elements and the minimum rate."""
    candidates = [minimum_rate]
    if include_earnings:
        candidates.append(earnings)
    if include_inflation:
        candidates.append(cpi)
    return max(candidates)


def rule_rate(inputs: UpratingYear) -> float:
    """The year's rate before any earnings-path top-up or override."""
    if not inputs.active:
        # s150A: at least the rise in earnings; no rise when earnings fall.
        return max(inputs.earnings, 0.0)
    return triple_lock_rate(
        inputs.earnings,
        inputs.cpi,
        inputs.minimum_rate,
        inputs.include_earnings,
        inputs.include_inflation,
    )


def uprating_rates(years: Dict[int, UpratingYear]) -> Dict[int, float]:
    """Uprating rate for each year, in year order.

    The earnings-path guarantee makes the rule path dependent. When it first
    applies, it anchors an earnings path at the pension's level in the year
    before; each guaranteed year the path grows by that year's earnings input,
    and the rate is raised, rounding up, to keep the pension on or above it.
    The path is dropped in any year the guarantee is off and re-anchored if it
    returns.
    """
    rates = {}
    level = 1.0
    earnings_path = None
    for year in sorted(years):
        inputs = years[year]
        rate = inputs.outturn if inputs.outturn is not None else rule_rate(inputs)
        if inputs.earnings_path_guarantee:
            if earnings_path is None:
                earnings_path = level
            earnings_path *= 1 + inputs.earnings
            if inputs.outturn is None:
                rate = max(
                    rate,
                    round_up_to_published_precision(earnings_path / level - 1),
                )
        else:
            earnings_path = None
        rates[year] = rate
        level *= 1 + rate
    return rates


def _flag(parameter: Parameter, instant: str) -> bool:
    value = parameter(instant)
    return bool(value) if value is not None else False


def uprating_years(parameters: ParameterNode) -> Iterable[int]:
    """Uprating years covered: from April 2011 to one year past the inputs."""
    return range(FIRST_UPRATING_YEAR, last_input_year(parameters) + 2)


def read_uprating_years(parameters: ParameterNode) -> Dict[int, UpratingYear]:
    """Collect each year's rule inputs from a parameter tree."""
    inputs = parameters.gov.economic_assumptions.statutory_uprating_inputs
    triple_lock = parameters.gov.dwp.state_pension.triple_lock

    years = {}
    for year in uprating_years(parameters):
        review_year = year - 1
        instant = uprating_instant(year)
        earnings = inputs.awe_total_pay_may_july(
            f"{review_year}-{AWE_OBSERVATION_MONTH_DAY}"
        )
        cpi = inputs.cpi_september(f"{review_year}-{CPI_OBSERVATION_MONTH_DAY}")
        # Null outside the overridden years.
        outturn = triple_lock.outturn(instant)
        if outturn is None and (earnings is None or cpi is None):
            raise ValueError(
                f"Missing statutory uprating input for April {year}: "
                f"May-July {review_year} earnings = {earnings}, "
                f"September {review_year} CPI = {cpi}."
            )
        years[year] = UpratingYear(
            earnings=round_to_published_precision(earnings or 0),
            cpi=round_to_published_precision(cpi or 0),
            minimum_rate=triple_lock.minimum_rate(instant),
            active=_flag(triple_lock.active, instant),
            include_earnings=_flag(triple_lock.include_earnings, instant),
            include_inflation=_flag(triple_lock.include_inflation, instant),
            earnings_path_guarantee=_flag(triple_lock.earnings_path_guarantee, instant),
            outturn=outturn,
        )
    return years


def add_triple_lock(parameters: ParameterNode) -> ParameterNode:
    """Add ``gov.economic_assumptions.yoy_growth.triple_lock``."""
    rates = uprating_rates(read_uprating_years(parameters))
    new_parameter = Parameter(
        "gov.economic_assumptions.yoy_growth.triple_lock",
        data={
            "description": (
                "State Pension uprating taking effect in April of each year."
            ),
            "values": {f"{year}-01-01": rate for year, rate in rates.items()},
            "metadata": {
                "unit": "/1",
                "label": "State Pension uprating rate",
            },
        },
    )
    parameters.gov.economic_assumptions.yoy_growth.add_child(
        "triple_lock", new_parameter
    )
    return parameters
