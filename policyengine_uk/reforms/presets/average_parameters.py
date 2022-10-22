from policyengine_core.parameters import ParameterNode, Parameter
from policyengine_core.periods import instant


def average_parameters(parameters: ParameterNode) -> ParameterNode:
    """Averages parameter values over each year."""
    for parameter in parameters.get_descendants():
        if isinstance(parameter, Parameter):
            for year in range(2019, 2029):
                values = []
                for month in range(1, 13):
                    values.append(parameter(instant(f"{year}-{month:02}-01")))
                try:
                    parameter.update(
                        period=f"year:{year}:1", value=sum(values) / 12
                    )
                except:
                    pass

    return parameters
