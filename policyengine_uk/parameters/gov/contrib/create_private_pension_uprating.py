from policyengine_core.parameters import (
    ParameterNode,
    Parameter,
)

YEARS = list(range(2020, 2035))


def add_private_pension_uprating_factor(
    parameters: ParameterNode,
) -> ParameterNode:
    values = {}
    rpi = parameters.gov.economic_assumptions.yoy_growth.obr.rpi
    for year in YEARS:
        values[f"{year}-01-01"] = min(rpi(year - 1), 0.05)
    new_parameter = Parameter(
        "gov.economic_assumptions.yoy_growth.obr.private_pension_index",
        data={
            "values": values,
        },
    )

    parameters.gov.economic_assumptions.yoy_growth.obr.add_child(
        "private_pension_index", new_parameter
    )
    return parameters
