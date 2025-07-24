from policyengine_core.parameters import Parameter, ParameterNode


def add_lagged_cpi(
    parameters: ParameterNode,
) -> ParameterNode:
    """
    Add lagged average earnings to the economic assumptions.
    """
    obr = parameters.gov.economic_assumptions.yoy_growth.obr
    cpi = obr.consumer_price_index

    lagged_cpi = Parameter(
        "gov.economic_assumptions.yoy_growth.obr.lagged_cpi",
        data={
            "values": {
                f"{year}-01-01": cpi(year - 1) for year in range(2010, 2030)
            },
        },
    )

    obr.add_child(
        "lagged_cpi",
        lagged_cpi,
    )

    return parameters
