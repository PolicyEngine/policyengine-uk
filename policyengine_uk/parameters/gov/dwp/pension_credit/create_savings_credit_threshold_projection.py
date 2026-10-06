"""Project Savings Credit thresholds from the two statutory uprating bases.

The maximum Savings Credit is the phase-in rate multiplied by the difference
between the standard minimum guarantee and the Savings Credit threshold. DWP
uprates the guarantee with earnings and the maximum with CPI. The threshold is
therefore a derived residual; applying CPI to it directly, or freezing it,
does not preserve the statutory relationship.
"""

from decimal import ROUND_HALF_UP, Decimal

from policyengine_core.parameters import ParameterNode

from policyengine_uk.parameters.gov.economic_assumptions.create_statutory_uprating_inputs import (
    CPI_OBSERVATION_MONTH_DAY,
    last_input_year,
)


BASE_YEAR = 2026
BASE_INSTANT = f"{BASE_YEAR}-04-01"
CURRENCY_PRECISION = Decimal("0.01")


def round_currency(amount: float) -> float:
    """Round a published weekly amount to the nearest penny, halves up."""
    return float(
        Decimal(repr(float(amount))).quantize(
            CURRENCY_PRECISION,
            ROUND_HALF_UP,
        )
    )


def project_maximum_savings_credit(amount: float, cpi_growth: float) -> float:
    """Project maximum Savings Credit without reducing its cash amount."""
    return amount * (1 + max(cpi_growth, 0))


def savings_credit_threshold(
    guarantee: float,
    maximum_savings_credit: float,
    phase_in_rate: float,
) -> float:
    """Solve the statutory maximum-Savings-Credit formula for its threshold."""
    if phase_in_rate <= 0:
        raise ValueError("The Savings Credit phase-in rate must be positive.")
    return guarantee - maximum_savings_credit / phase_in_rate


def add_savings_credit_threshold_projection(
    parameters: ParameterNode,
) -> ParameterNode:
    """Add future thresholds consistent with projected guarantee and maximum."""
    savings_credit = parameters.gov.dwp.pension_credit.savings_credit
    guarantees = parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    earnings_index = (
        parameters.gov.economic_assumptions.indices.statutory_earnings_floor
    )
    cpi_september = (
        parameters.gov.economic_assumptions.statutory_uprating_inputs.cpi_september
    )
    base_phase_in_rate = float(savings_credit.rate.phase_in(BASE_INSTANT))
    base_earnings_index = float(earnings_index(BASE_INSTANT))
    relationship_parameters = {
        "SINGLE": (guarantees.SINGLE, savings_credit.threshold.SINGLE),
        "COUPLE": (guarantees.COUPLE, savings_credit.threshold.COUPLE),
    }

    for guarantee_parameter, threshold_parameter in relationship_parameters.values():
        base_guarantee = float(guarantee_parameter(BASE_INSTANT))
        base_threshold = float(threshold_parameter(BASE_INSTANT))
        maximum = round_currency(base_phase_in_rate * (base_guarantee - base_threshold))
        for year in range(BASE_YEAR + 1, last_input_year(parameters) + 2):
            observation_year = year - 1
            maximum = project_maximum_savings_credit(
                maximum,
                float(cpi_september(f"{observation_year}-{CPI_OBSERVATION_MONTH_DAY}")),
            )
            guarantee = base_guarantee * (
                float(earnings_index(f"{year}-04-01")) / base_earnings_index
            )
            threshold_parameter.update(
                period=f"year:{year}-04-01:1",
                value=savings_credit_threshold(
                    guarantee,
                    maximum,
                    float(savings_credit.rate.phase_in(f"{year}-04-01")),
                ),
            )
    return parameters
