"""Project protected pension-age Housing Benefit allowances by component.

The protected allowances consist of the corresponding Pension Credit
standard minimum guarantee plus a retained Savings Credit uplift. The
guarantee component follows the shared statutory earnings index; the retained
uplift follows non-negative September CPI. Projecting either whole allowance
with one series would therefore misstate its relationship to Pension Credit.
"""

from policyengine_core.parameters import Parameter, ParameterNode

from policyengine_uk.parameters.gov.economic_assumptions.create_statutory_uprating_inputs import (
    CPI_OBSERVATION_MONTH_DAY,
    last_input_year,
)


BASE_YEAR = 2026
BASE_INSTANT = f"{BASE_YEAR}-04-01"


def project_retained_uplift(amount: float, cpi_growth: float) -> float:
    """Project the retained Savings Credit uplift without a cash reduction."""
    return amount * (1 + max(cpi_growth, 0))


def protected_allowance_index_values(
    base_allowance: float,
    guarantee_component: float,
    earnings_index: Parameter,
    cpi_september: Parameter,
    final_observation_year: int,
) -> dict[str, float]:
    """Build a component-weighted index from the last enacted allowance."""
    retained_uplift = base_allowance - guarantee_component
    if retained_uplift < 0:
        raise ValueError(
            "The protected Housing Benefit allowance cannot be lower than "
            "the corresponding Pension Credit guarantee."
        )

    base_earnings_index = float(earnings_index(BASE_INSTANT))
    values = {BASE_INSTANT: 1.0}
    for year in range(BASE_YEAR + 1, final_observation_year + 2):
        observation_year = year - 1
        guarantee = guarantee_component * (
            float(earnings_index(f"{year}-04-01")) / base_earnings_index
        )
        retained_uplift = project_retained_uplift(
            retained_uplift,
            float(cpi_september(f"{observation_year}-{CPI_OBSERVATION_MONTH_DAY}")),
        )
        values[f"{year}-04-01"] = (guarantee + retained_uplift) / base_allowance
    return values


def _projection_parameter(
    relationship: str,
    base_allowance: float,
    guarantee_component: float,
    earnings_index: Parameter,
    cpi_september: Parameter,
    final_observation_year: int,
) -> Parameter:
    retained_uplift = base_allowance - guarantee_component
    relationship_label = (
        "single and lone-parent" if relationship == "single" else "couple"
    )
    return Parameter(
        (
            "gov.dwp.housing_benefit.allowances."
            f"protected_pension_age_uprating.{relationship}"
        ),
        data={
            "description": (
                f"Forecast index for the protected {relationship_label} "
                "pension-age Housing Benefit allowance. The enacted 2026-27 "
                f"base comprises a £{guarantee_component:g} Pension Credit "
                f"guarantee and a £{retained_uplift:g} retained Savings "
                "Credit uplift. The components follow the shared statutory "
                "earnings index and non-negative September CPI, respectively. "
                "Projected values are not enacted rates."
            ),
            "values": protected_allowance_index_values(
                base_allowance,
                guarantee_component,
                earnings_index,
                cpi_september,
                final_observation_year,
            ),
            "metadata": {
                "unit": "/1",
                "label": (
                    f"Protected {relationship_label} pension-age Housing "
                    "Benefit allowance forecast index"
                ),
                "reference": [
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
                            "A14/2025 Housing Benefit uprating for the "
                            "financial year ending March 2027, paragraphs "
                            "5, 6 and 20"
                        ),
                        "href": (
                            "https://www.gov.uk/government/publications/"
                            "housing-benefit-adjudication-circulars-2025/"
                            "a142025-housing-benefit-uprating-for-the-"
                            "financial-year-ending-march-2027"
                        ),
                    },
                    {
                        "title": (
                            "ONS KAC3 average weekly earnings, whole economy, total pay"
                        ),
                        "href": (
                            "https://www.ons.gov.uk/"
                            "employmentandlabourmarket/peopleinwork/"
                            "earningsandworkinghours/timeseries/kac3/lms"
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


def add_protected_pension_age_uprating(
    parameters: ParameterNode,
) -> ParameterNode:
    """Add relationship-specific protected-allowance forecast indices."""
    allowances = parameters.gov.dwp.housing_benefit.allowances
    guarantees = parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    earnings_index = (
        parameters.gov.economic_assumptions.indices.statutory_earnings_floor
    )
    cpi_september = (
        parameters.gov.economic_assumptions.statutory_uprating_inputs.cpi_september
    )
    projection = ParameterNode(
        name=("gov.dwp.housing_benefit.allowances.protected_pension_age_uprating"),
        data={},
    )
    allowances.add_child("protected_pension_age_uprating", projection)

    relationship_parameters = {
        "single": (allowances.single.aged, guarantees.SINGLE),
        "couple": (allowances.couple.aged, guarantees.COUPLE),
    }
    final_observation_year = last_input_year(parameters)
    for relationship, (allowance, guarantee) in relationship_parameters.items():
        projection.add_child(
            relationship,
            _projection_parameter(
                relationship,
                float(allowance(BASE_INSTANT)),
                float(guarantee(BASE_INSTANT)),
                earnings_index,
                cpi_september,
                final_observation_year,
            ),
        )
    return parameters
