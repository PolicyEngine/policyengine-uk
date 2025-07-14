from policyengine_core.parameters import Parameter, ParameterNode


def add_lagged_earnings(
    parameters: ParameterNode,
) -> ParameterNode:
    """
    Add lagged average earnings to the economic assumptions.
    """
    obr = parameters.gov.economic_assumptions.yoy_growth.obr
    earnings = obr.average_earnings

    lagged_earnings = Parameter(
        "gov.economic_assumptions.yoy_growth.lagged_average_earnings",
        data={
            "values": {
                f"{year}-01-01": earnings(year - 1)
                for year in range(2022, 2030)
            },
        },
    )

    obr.add_child(
        "lagged_average_earnings",
        lagged_earnings,
    )

    return parameters
