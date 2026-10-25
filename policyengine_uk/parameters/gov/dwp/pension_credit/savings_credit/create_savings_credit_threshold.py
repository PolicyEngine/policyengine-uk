"""Build Savings Credit threshold indices from the statutory uprating bases.

The maximum Savings Credit is the phase-in rate multiplied by the difference
between the standard minimum guarantee and the Savings Credit threshold. DWP
uprates the guarantee with earnings and the maximum with CPI. The threshold is
therefore a derived residual; applying CPI to it directly, or freezing it,
does not preserve the statutory relationship. Each generated index is applied
by the standard parameter-uprating operation, so explicit threshold values and
reforms remain authoritative anchors. The indices start from the last year
with enacted rates (pension_age_projection_base.py).
"""

from decimal import ROUND_HALF_UP, Decimal, localcontext
from sys import float_info

from policyengine_core.parameters import Parameter, ParameterNode

from policyengine_uk.parameters.gov.dwp.pension_credit.pension_age_projection_base import (
    projection_base_year,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_statutory_uprating_inputs import (
    CPI_OBSERVATION_MONTH_DAY,
)


CURRENCY_PRECISION = Decimal("0.01")


def projection_instant(year: int) -> str:
    """Return the date sampled by fiscal-year parameter conversion."""
    return f"{year}-04-30"


def round_currency(amount: float) -> float:
    """Round a published weekly amount to the nearest penny, halves up."""
    value = Decimal(repr(float(amount)))
    with localcontext() as context:
        context.prec = max(28, value.adjusted() + 4)
        return float(value.quantize(CURRENCY_PRECISION, ROUND_HALF_UP))


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


def threshold_index_values(
    base_guarantee: float,
    base_threshold: float,
    phase_in_rate: Parameter,
    earnings_index: Parameter,
    cpi_september: Parameter,
    final_observation_year: int,
    *,
    base_year: int,
    base_maximum: float | None = None,
    price_index: Parameter | None = None,
) -> dict[str, float]:
    """Build a forecast index from the last enacted threshold."""
    base_instant = f"{base_year}-04-01"
    if base_threshold <= 0:
        # The index scales the base, so a reform's zero threshold stays zero.
        return {base_instant: 1.0}
    base_phase_in_rate = float(phase_in_rate(projection_instant(base_year)))
    maximum = (
        max(0, round_currency(base_phase_in_rate * (base_guarantee - base_threshold)))
        if base_maximum is None
        else base_maximum
    )
    base_earnings_index = float(earnings_index(base_instant))
    values = {base_instant: 1.0}

    for year in range(base_year + 1, final_observation_year + 2):
        observation_year = year - 1
        growth = (
            float(price_index(f"{year}-04-01"))
            / float(price_index(f"{year - 1}-04-01"))
            - 1
            if price_index is not None
            else float(cpi_september(f"{observation_year}-{CPI_OBSERVATION_MONTH_DAY}"))
        )
        maximum = project_maximum_savings_credit(maximum, growth)
        guarantee = base_guarantee * (
            float(earnings_index(f"{year}-04-01")) / base_earnings_index
        )
        phase_in = float(phase_in_rate(projection_instant(year)))
        threshold = (
            max(0, savings_credit_threshold(guarantee, maximum, phase_in))
            if phase_in > 0
            else values[f"{year - 1}-04-01"] * base_threshold
        )
        # An exact zero index cannot anchor a later explicit reform (Core
        # divides by the index at that anchor). Keep a positive, finite
        # index even when the non-negative residual reaches zero or the
        # reformed base is subnormal; ordinary monetary bases are unchanged.
        ratio = threshold / base_threshold
        values[f"{year}-04-01"] = min(max(ratio, float_info.min), float_info.max)

    return values


def _projection_parameter(
    relationship: str,
    base_guarantee: float,
    base_threshold: float,
    phase_in_rate: Parameter,
    earnings_index: Parameter,
    cpi_september: Parameter,
    final_observation_year: int,
    base_year: int,
    base_maximum: float,
    price_index: Parameter,
) -> Parameter:
    relationship_label = relationship.lower()
    return Parameter(
        (f"gov.dwp.pension_credit.savings_credit.threshold_uprating.{relationship}"),
        data={
            "description": (
                f"Forecast index for the {relationship_label} Savings Credit "
                "threshold. It derives the threshold from an earnings-projected "
                "standard minimum guarantee and a maximum Savings Credit amount "
                "projected by non-negative September CPI. Explicit threshold "
                "values remain authoritative. Projected values are not enacted "
                "rates."
            ),
            "values": threshold_index_values(
                base_guarantee,
                base_threshold,
                phase_in_rate,
                earnings_index,
                cpi_september,
                final_observation_year,
                base_year=base_year,
                base_maximum=base_maximum,
                price_index=price_index,
            ),
            "metadata": {
                "unit": "/1",
                "label": (
                    f"Pension Credit Savings Credit {relationship_label} "
                    "threshold forecast index"
                ),
                "reference": [
                    {
                        "title": "State Pension Credit Act 2002 section 3",
                        "href": (
                            "https://www.legislation.gov.uk/ukpga/2002/16/section/3"
                        ),
                    },
                    {
                        "title": (
                            "Social Security Administration Act 1992 section 150"
                        ),
                        "href": (
                            "https://www.legislation.gov.uk/ukpga/1992/5/section/150"
                        ),
                    },
                    {
                        "title": (
                            "Social Security Administration Act 1992 section 150A"
                        ),
                        "href": (
                            "https://www.legislation.gov.uk/ukpga/1992/5/section/150A"
                        ),
                    },
                    {
                        "title": (
                            "Social Security Administration (Northern Ireland) "
                            "Act 1992 section 132"
                        ),
                        "href": (
                            "https://www.legislation.gov.uk/ukpga/1992/8/section/132"
                        ),
                    },
                    {
                        "title": (
                            "Social Security Administration (Northern Ireland) "
                            "Act 1992 section 132A"
                        ),
                        "href": (
                            "https://www.legislation.gov.uk/ukpga/1992/8/section/132A"
                        ),
                    },
                    {
                        "title": (
                            "A14/2025 Housing Benefit uprating for the financial "
                            "year ending March 2027"
                        ),
                        "href": (
                            "https://www.gov.uk/government/publications/"
                            "housing-benefit-adjudication-circulars-2025/"
                            "a142025-housing-benefit-uprating-for-the-financial-"
                            "year-ending-march-2027"
                        ),
                    },
                    {
                        "title": (
                            "ONS KAC3 average weekly earnings, whole economy, total pay"
                        ),
                        "href": (
                            "https://www.ons.gov.uk/employmentandlabourmarket/"
                            "peopleinwork/earningsandworkinghours/timeseries/"
                            "kac3/lms"
                        ),
                    },
                    {
                        "title": "ONS D7G7 Consumer Prices Index annual rate",
                        "href": (
                            "https://www.ons.gov.uk/economy/"
                            "inflationandpriceindices/timeseries/d7g7/mm23"
                        ),
                    },
                ],
            },
        },
    )


def last_projected_year(parameters: ParameterNode) -> int:
    """Last year of main's earnings projection."""
    index = parameters.gov.economic_assumptions.indices.earnings_uprating
    return max(int(entry.instant_str[:4]) for entry in index.values_list)


def enacted_maximum(
    parameters: ParameterNode, relationship: str, base_year: int
) -> float:
    """Use the published maximum; a newer complete rates entry resets its base."""
    pc = parameters.gov.dwp.pension_credit
    maximum = getattr(pc.savings_credit.maximum, relationship)
    if max(int(entry.instant_str[:4]) for entry in maximum.values_list) >= base_year:
        return max(0, float(maximum(projection_instant(base_year))))
    guarantee = getattr(pc.guarantee_credit.minimum_guarantee, relationship)
    threshold = getattr(pc.savings_credit.threshold, relationship)
    at = projection_instant(base_year)
    return max(
        0,
        round_currency(
            float(pc.savings_credit.rate.phase_in(at))
            * (float(guarantee(at)) - float(threshold(at)))
        ),
    )


def project_savings_credit_threshold(
    parameters: ParameterNode,
    unreformed: ParameterNode | None = None,
) -> ParameterNode:
    """Add forecast indices for each Savings Credit threshold.

    The separately set threshold is not re-derived by a guarantee or
    phase-in reform, including a reform to the projection's base year. Use
    the unreformed guarantee unless the corresponding threshold base changes,
    in which case use the reformed pair, and the enacted phase-in rate, so a
    phase-in reform (to zero, say) changes the Savings Credit paid and not the
    threshold. Earnings and CPI inputs come from the reform's tree.
    """
    savings_credit = parameters.gov.dwp.pension_credit.savings_credit
    projection_base = parameters if unreformed is None else unreformed
    base_year = projection_base_year(projection_base)
    base_instant = projection_instant(base_year)
    enacted_savings_credit = projection_base.gov.dwp.pension_credit.savings_credit
    base_thresholds = enacted_savings_credit.threshold
    guarantees = (
        projection_base.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    )
    reformed_guarantees = (
        parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    )
    earnings_index = parameters.gov.economic_assumptions.indices.earnings_uprating
    cpi_september = (
        parameters.gov.economic_assumptions.statutory_uprating_inputs.cpi_september
    )
    projection = ParameterNode(
        name=("gov.dwp.pension_credit.savings_credit.threshold_uprating"),
        data={},
    )
    savings_credit.add_child("threshold_uprating", projection)
    relationship_parameters = {
        "SINGLE": (guarantees.SINGLE, base_thresholds.SINGLE),
        "COUPLE": (guarantees.COUPLE, base_thresholds.COUPLE),
    }
    final_observation_year = last_projected_year(parameters) - 1
    # gov.benefit_uprating_cpi is a YAML alias until parameter propagation.
    # Read its concrete generated September-CPI index at this generation stage.
    price_index = parameters.gov.economic_assumptions.indices.september_cpi_uprating
    for relationship, (
        guarantee_parameter,
        threshold_parameter,
    ) in relationship_parameters.items():
        maximum = enacted_maximum(projection_base, relationship, base_year)
        maximum_parameter = getattr(savings_credit.maximum, relationship)
        if (
            max(int(entry.instant_str[:4]) for entry in maximum_parameter.values_list)
            < base_year
        ):
            maximum_parameter.update(start=f"{base_year}-04-01", value=maximum)
        reformed_threshold = getattr(savings_credit.threshold, relationship)
        if reformed_threshold(base_instant) != threshold_parameter(base_instant):
            threshold_parameter = reformed_threshold
            guarantee_parameter = getattr(reformed_guarantees, relationship)
            maximum = max(
                0,
                round_currency(
                    float(enacted_savings_credit.rate.phase_in(base_instant))
                    * (
                        float(guarantee_parameter(base_instant))
                        - float(threshold_parameter(base_instant))
                    )
                ),
            )
        projection.add_child(
            relationship,
            _projection_parameter(
                relationship,
                float(guarantee_parameter(base_instant)),
                float(threshold_parameter(base_instant)),
                enacted_savings_credit.rate.phase_in,
                earnings_index,
                cpi_september,
                final_observation_year,
                base_year,
                maximum,
                price_index,
            ),
        )
    return parameters
