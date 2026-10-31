from policyengine_core.parameters import (
    ParameterNode,
    Parameter,
    get_parameter,
)


def last_year(parameter: Parameter) -> int:
    """The first year whose 1 January reads the parameter's final value."""
    final_instant = max(value.instant_str for value in parameter.values_list)
    year = int(final_instant[:4])
    return year if final_instant.endswith("-01-01") else year + 1


def growth_horizon(yoy_growth: ParameterNode) -> int:
    """The last year any growth series covers, where the indices end.

    The indices read each series on 1 January, so a value dated later in a
    year first reaches them the year after. Pass the series as the builder
    sees them: fiscal conversion moves a value dated before May to that year's
    January, so a converted series can report a year less.
    """
    return max(
        (
            last_year(parameter)
            for parameter in yoy_growth.get_descendants()
            if isinstance(parameter, Parameter)
        ),
        default=0,
    )


def create_economic_assumption_indices(
    parameters: ParameterNode,
) -> ParameterNode:
    econ_assumptions: ParameterNode = parameters.gov.economic_assumptions
    yoy_growth: ParameterNode = econ_assumptions.yoy_growth
    horizon = growth_horizon(yoy_growth)
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
            values = {start_year: 1.0}

            for year in range(start_year + 1, horizon + 1):
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
