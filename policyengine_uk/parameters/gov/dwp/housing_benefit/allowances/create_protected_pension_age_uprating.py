"""Project the protected pension-age Housing Benefit allowance.

The protected single and lone-parent allowance consists of the Pension Credit
standard minimum guarantee plus the retained Savings Credit uplift. The two
components use different annual review inputs, so neither CPI nor earnings
alone is a faithful forecast proxy.
"""

from policyengine_core.parameters import Parameter, ParameterNode


BASE_YEAR = 2026
GUARANTEE_COMPONENT = 238.0
SAVINGS_CREDIT_COMPONENT = 18.0
BASE_ALLOWANCE = GUARANTEE_COMPONENT + SAVINGS_CREDIT_COMPONENT


def project_components(
    guarantee: float,
    savings_credit_uplift: float,
    earnings_growth: float,
    cpi_growth: float,
) -> tuple[float, float]:
    """Project both components without reducing either cash amount."""
    return (
        guarantee * (1 + max(earnings_growth, 0)),
        savings_credit_uplift * (1 + max(cpi_growth, 0)),
    )


def add_protected_pension_age_uprating(
    parameters: ParameterNode,
) -> ParameterNode:
    """Add the component-weighted forecast index used after April 2026."""
    inputs = parameters.gov.economic_assumptions.statutory_uprating_inputs
    allowances = parameters.gov.dwp.housing_benefit.allowances
    last_input_year = min(
        max(
            int(value.instant_str[:4])
            for value in input_parameter.values_list
            if value.value is not None
        )
        for input_parameter in (
            inputs.awe_total_pay_may_july,
            inputs.cpi_september,
        )
    )

    guarantee = GUARANTEE_COMPONENT
    savings_credit_uplift = SAVINGS_CREDIT_COMPONENT
    values = {f"{BASE_YEAR}-04-01": 1.0}
    for year in range(BASE_YEAR + 1, last_input_year + 2):
        observation_year = year - 1
        guarantee, savings_credit_uplift = project_components(
            guarantee,
            savings_credit_uplift,
            float(inputs.awe_total_pay_may_july(f"{observation_year}-07-01")),
            float(inputs.cpi_september(f"{observation_year}-09-01")),
        )
        values[f"{year}-04-01"] = (guarantee + savings_credit_uplift) / BASE_ALLOWANCE

    allowances.add_child(
        "protected_pension_age_uprating",
        Parameter(
            "gov.dwp.housing_benefit.allowances.protected_pension_age_uprating",
            data={
                "description": (
                    "Forecast index for the protected pension-age Housing "
                    "Benefit allowance. The 2026-27 rounded base allocates "
                    "£238 to the Pension Credit guarantee and £18 to the "
                    "retained Savings Credit uplift. The components follow "
                    "non-negative May-to-July earnings and September CPI, "
                    "respectively. Projected values are not enacted rates."
                ),
                "values": values,
                "metadata": {
                    "unit": "/1",
                    "label": (
                        "Protected pension-age Housing Benefit allowance forecast index"
                    ),
                    "reference": [
                        {
                            "title": (
                                "A14/2025 Housing Benefit uprating for the "
                                "financial year ending March 2027, paragraphs "
                                "5 and 20"
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
                                "ONS KAC3 average weekly earnings, whole "
                                "economy, total pay"
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
        ),
    )
    return parameters
