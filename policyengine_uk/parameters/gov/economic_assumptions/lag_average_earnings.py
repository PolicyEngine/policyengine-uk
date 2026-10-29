from policyengine_core.parameters import ParameterNode

from policyengine_uk.parameters.gov.economic_assumptions.lagged_series import (
    add_lagged_parameter,
)


def add_lagged_earnings(
    parameters: ParameterNode,
) -> ParameterNode:
    """
    Add lagged average earnings to the economic assumptions.
    """
    obr = parameters.gov.economic_assumptions.yoy_growth.obr
    # Anchor the index at 1 on 1 January 2021 so it includes the 2022
    # growth (2021 earnings growth), the first listed (#2692).
    add_lagged_parameter(
        obr,
        "average_earnings",
        "lagged_average_earnings",
        first_year=2022,
        metadata={"index_base_year": 2021},
    )

    return parameters
