from policyengine_core.parameters import (
    ParameterNode,
    Parameter,
    get_parameter,
)


def create_economic_assumption_indices(
    parameters: ParameterNode,
) -> ParameterNode:
    econ_assumptions: ParameterNode = parameters.gov.economic_assumptions
    yoy_growth: ParameterNode = econ_assumptions.yoy_growth
    # Index levels dated 1 January, one per calendar year, so a bare-year
    # reform key names the calendar year (policyengine_uk.utils.dated_reforms).
    indices = ParameterNode(
        name="gov.economic_assumptions.indices",
        data={"metadata": {"calendar_year_series": True}},
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
            # By default the first growth year is the index base, so its
            # growth is not in the index. A series can set
            # `index_base_year` to an earlier year to anchor the index there
            # instead, so the first growth step is included. The anchor is
            # an index level of 1, not a growth observation.
            base_year = (descendant.metadata or {}).get("index_base_year")
            if base_year is None:
                base_year = start_year
            elif base_year >= start_year:
                raise ValueError(
                    f"{full_name}: index_base_year {base_year} must be before "
                    f"the first growth year {start_year}."
                )
            start_year = base_year
            values = {start_year: 1.0}

            for year in range(start_year + 1, 2040):
                yoy_growth = descendant(year)
                indices_value = values[year - 1] * (1 + yoy_growth)
                # Rounding an earnings index down can put the projected
                # guarantee below its statutory annual earnings floor.
                if full_name != "gov.economic_assumptions.yoy_growth.earnings_uprating":
                    indices_value = round(indices_value, 5)
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
