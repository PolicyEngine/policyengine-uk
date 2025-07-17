from policyengine_core.parameters import (
    ParameterNode,
    Parameter,
    get_parameter,
)


def create_economic_assumption_indices(
    parameters: ParameterNode,
) -> ParameterNode:
    econ_assumptions: ParameterNode = parameters.gov.economic_assumptions

    indices = ParameterNode(
        name="gov.economic_assumptions.indices",
        data={},
    )
    econ_assumptions.add_child("indices", indices)

    # Process both yoy_growth and regional_private_rent_yoy_growth
    source_nodes = [
        (econ_assumptions.yoy_growth, "yoy_growth"),
        (
            econ_assumptions.regional_private_rent_yoy_growth,
            "regional_private_rent_yoy_growth",
        ),
    ]

    for source_node, source_name in source_nodes:
        for descendant in source_node.get_descendants():
            parent_node = parameters.get_child(
                descendant.parent.name.replace(source_name, "indices")
            )
            child_name = descendant.name.split(".")[-1]

            if isinstance(descendant, ParameterNode):
                mirror_node = ParameterNode(
                    name=descendant.name.replace(source_name, "indices"),
                    data={},
                )
                parent_node.add_child(child_name, mirror_node)
            else:
                start_year = int(descendant.values_list[-1].instant_str[:4])
                values = {start_year: 1.0}

                for year in range(start_year + 1, 2030):
                    yoy_growth = descendant(year)
                    indices_value = round(
                        values[year - 1] * (1 + yoy_growth), 5
                    )
                    values[year] = indices_value

                mirror_parameter = Parameter(
                    name=descendant.name.replace(source_name, "indices"),
                    data={
                        "values": {
                            f"{year}-01-01": value
                            for year, value in values.items()
                        },
                    },
                )
                parent_node.add_child(child_name, mirror_parameter)

    return parameters
