from policyengine_core.parameters import (
    ParameterNode,
    Parameter,
)

YEARS = list(range(2020, 2035))


def add_private_pension_uprating_factor(
    parameters: ParameterNode,
) -> ParameterNode:
    values = {}
    rpi = parameters.gov.economic_assumptions.indices.obr.rpi
    last_value = rpi(YEARS[0] - 1)
    for year in YEARS:
        value = rpi(year - 1)
        rel_change = value / rpi(year - 2)
        rel_change = min(rel_change, 1.05)
        new_index = last_value * rel_change
        last_value = new_index
        values[f"{year}-01-01"] = new_index
    new_parameter = Parameter(
        "gov.economic_assumptions.indices.obr.private_pension_index",
        data={
            "values": values,
        },
    )

    parameters.gov.economic_assumptions.indices.obr.add_child(
        "private_pension_index", new_parameter
    )
    return parameters
