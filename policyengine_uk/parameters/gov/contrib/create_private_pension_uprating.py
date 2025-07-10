from policyengine_core.parameters import (
    ParameterNode,
    Parameter,
)

YEARS = list(range(2010, 2035))


def add_private_pension_uprating_factor(
    parameters: ParameterNode,
) -> ParameterNode:
    values = {}
    rpi = parameters.gov.obr.rpi
    last_value = rpi(2008)
    for year in YEARS:
        value = rpi(year - 1)
        rel_change = value / rpi(year - 2)
        rel_change = min(rel_change, 1.05)
        new_index = last_value * rel_change
        last_value = new_index
        values[f"{year}-01-01"] = new_index
    new_parameter = Parameter(
        "gov.obr.private_pension_index",
        data={
            "values": values,
        },
    )

    parameters.gov.obr.add_child("private_pension_index", new_parameter)
    return parameters
