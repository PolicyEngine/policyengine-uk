from policyengine_core.parameters import (
    ParameterNode,
    Parameter,
    get_parameter,
)

from policyengine_uk.parameters.gov.economic_assumptions.horizon import (
    growth_horizon,
)


def create_economic_assumption_indices(
    parameters: ParameterNode,
) -> ParameterNode:
    econ_assumptions: ParameterNode = parameters.gov.economic_assumptions
    yoy_growth: ParameterNode = econ_assumptions.yoy_growth
    # Every index runs to the last year the growth series cover. A series
    # that ends sooner holds its final growth rate to that year.
    horizon = growth_horizon(yoy_growth)
    indices = ParameterNode(
        name="gov.economic_assumptions.indices",
        data={},
    )
    econ_assumptions.add_child(
        "indices",
        indices,
    )

    for descendant in yoy_growth.get_descendants():
        parent_node = parameters.get_child(
            descendant.parent.name.replace("yoy_growth", "indices")
        )
        full_name = descendant.name
        child_name = full_name.split(".")[-1]
        if isinstance(descendant, ParameterNode):
            mirror_node = ParameterNode(
                name=descendant.name.replace("yoy_growth", "indices"),
                data={},
            )
            parent_node.add_child(
                child_name,
                mirror_node,
            )
        else:
            start_year = int(descendant.values_list[-1].instant_str[:4])
            values = {start_year: 1.0}

            for year in range(start_year + 1, horizon + 1):
                growth = descendant(year)
                indices_value = round(
                    values[year - 1] * (1 + growth),
                    5,
                )
                values[year] = indices_value

            mirror_parameter = Parameter(
                name=descendant.name.replace("yoy_growth", "indices"),
                data={
                    "values": {
                        f"{year}-01-01": value for year, value in values.items()
                    },
                },
            )

            parent_node.add_child(
                child_name,
                mirror_parameter,
            )

    return parameters
