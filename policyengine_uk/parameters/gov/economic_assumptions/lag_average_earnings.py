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
    add_lagged_parameter(
        obr, "average_earnings", "lagged_average_earnings", first_year=2022
    )

    return parameters
