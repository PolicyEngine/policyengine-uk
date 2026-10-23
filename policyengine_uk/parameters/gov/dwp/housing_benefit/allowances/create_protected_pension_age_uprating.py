"""Project protected pension-age Housing Benefit allowances by component.

The protected allowances consist of the corresponding Pension Credit
standard minimum guarantee plus a retained Savings Credit uplift. The
guarantee component follows the shared statutory earnings index; the retained
uplift follows non-negative September CPI. Projecting either whole allowance
with one series would therefore misstate its relationship to Pension Credit.
The indices start from the last year with enacted rates
(pension_age_projection_base.py).
"""

from policyengine_core.parameters import Parameter, ParameterNode

from policyengine_uk.parameters.gov.dwp.pension_credit.pension_age_projection_base import (
    projection_base_year,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_statutory_uprating_inputs import (
    CPI_OBSERVATION_MONTH_DAY,
    last_input_year,
)


# Each protected allowance, with the standard minimum guarantee it holds.
ALLOWANCE_GUARANTEES = {"single": "SINGLE", "lone_parent": "SINGLE", "couple": "COUPLE"}


def base_instant(base_year: int) -> str:
    return f"{base_year}-04-01"


def project_retained_uplift(amount: float, cpi_growth: float) -> float:
    """Project the retained Savings Credit uplift without a cash reduction."""
    return amount * (1 + max(cpi_growth, 0))


def protected_allowance_index_values(
    base_allowance: float,
    guarantee_component: float,
    earnings_index: Parameter,
    cpi_september: Parameter,
    final_observation_year: int,
    *,
    base_year: int,
) -> dict[str, float]:
    """Build a component-weighted index from the last enacted allowance."""
    retained_uplift = base_allowance - guarantee_component
    if retained_uplift < 0:
        raise ValueError(
            "The protected Housing Benefit allowance cannot be lower than "
            "the corresponding Pension Credit guarantee."
        )
    start = base_instant(base_year)
    if base_allowance <= 0:
        # The index scales the base, so a reform's zero allowance stays zero.
        return {start: 1.0}

    base_earnings_index = float(earnings_index(start))
    values = {start: 1.0}
    for year in range(base_year + 1, final_observation_year + 2):
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
    allowance: str,
    base_allowance: float,
    guarantee_component: float,
    earnings_index: Parameter,
    cpi_september: Parameter,
    final_observation_year: int,
    base_year: int,
) -> Parameter:
    retained_uplift = base_allowance - guarantee_component
    relationship_label = allowance.replace("_", "-")
    fiscal_year = f"{base_year}-{(base_year + 1) % 100:02d}"
    return Parameter(
        (
            "gov.dwp.housing_benefit.allowances."
            f"protected_pension_age_uprating.{allowance}"
        ),
        data={
            "description": (
                f"Forecast index for the protected {relationship_label} "
                f"pension-age Housing Benefit allowance. The {fiscal_year} "
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
                base_year=base_year,
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
    unreformed: ParameterNode | None = None,
) -> ParameterNode:
    """Add a protected-allowance forecast index for each allowance.

    A guarantee reform does not re-derive the separately set HB allowance:
    each index uses the unreformed guarantee unless its own allowance base
    changes, when it uses the reformed pair. A reformed allowance below its
    guarantee keeps no retained Savings Credit, so it is projected whole with
    the guarantee's earnings path, as an allowance equal to its guarantee is.
    The enacted pair is still validated, so a rates update that puts an
    allowance below its guarantee fails. Earnings and CPI inputs come from
    the reform's parameter tree.
    """
    allowances = parameters.gov.dwp.housing_benefit.allowances
    projection_base = parameters if unreformed is None else unreformed
    base_year = projection_base_year(projection_base)
    start = base_instant(base_year)
    base_allowances = projection_base.gov.dwp.housing_benefit.allowances
    reformed_guarantees = (
        parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    )
    guarantees = (
        projection_base.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    )
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

    final_observation_year = last_input_year(parameters)
    for allowance_name, relationship in ALLOWANCE_GUARANTEES.items():
        allowance = float(getattr(base_allowances, allowance_name).aged(start))
        guarantee = float(getattr(guarantees, relationship)(start))
        reformed_allowance = float(getattr(allowances, allowance_name).aged(start))
        if reformed_allowance != allowance:
            allowance = reformed_allowance
            guarantee = min(
                float(getattr(reformed_guarantees, relationship)(start)),
                reformed_allowance,
            )
        projection.add_child(
            allowance_name,
            _projection_parameter(
                allowance_name,
                allowance,
                guarantee,
                earnings_index,
                cpi_september,
                final_observation_year,
                base_year,
            ),
        )
    return parameters
