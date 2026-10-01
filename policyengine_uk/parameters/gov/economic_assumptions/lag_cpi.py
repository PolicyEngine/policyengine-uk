from policyengine_core.parameters import ParameterNode

from policyengine_uk.parameters.gov.economic_assumptions.lagged_series import (
    add_lagged_parameter,
)


def add_lagged_cpi(
    parameters: ParameterNode,
) -> ParameterNode:
    """
    Add lagged CPI to the economic assumptions.
    """
    obr = parameters.gov.economic_assumptions.yoy_growth.obr
    add_lagged_parameter(obr, "consumer_price_index", "lagged_cpi", first_year=2010)

    return parameters
