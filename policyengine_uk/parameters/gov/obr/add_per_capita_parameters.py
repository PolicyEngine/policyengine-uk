from policyengine_core.parameters import (
    ParameterNode,
    Parameter,
    get_parameter,
)

PARAMETERS_TO_ADD_FOR = [
    "gov.obr.employment_income",
    "gov.obr.mixed_income",
    "gov.obr.non_labour_income",
]

YEARS = list(range(2022, 2035))


def add_per_capita_parameters(parameters: ParameterNode) -> ParameterNode:
    population = parameters.gov.ons.population

    new_node = ParameterNode("gov.obr.per_capita", data={})

    for parameter in PARAMETERS_TO_ADD_FOR:
        parameter_node: ParameterNode = get_parameter(parameters, parameter)
        values = {}
        for year in YEARS:
            parameter_per_capita = round(
                parameter_node(year) * 1e9 / population(year)
            )
            values[f"{year}-01-01"] = parameter_per_capita
        name = f"{parameter}.per_capita.{parameter_node.name.split('.')[-1]}"
        new_parameter = Parameter(
            name,
            data={
                "values": values,
            },
        )
        new_node.add_child(name, new_parameter)

    parameters.gov.obr.add_child("gov.obr.per_capita", new_node)
    return parameters
