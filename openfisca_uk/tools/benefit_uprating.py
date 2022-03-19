from openfisca_core.parameters import ParameterNode, Parameter
from openfisca_core.periods import instant

def add_benefit_uprating(parameters: ParameterNode) -> ParameterNode:
    """Adds the September CPI parameter.
    """
    cpi = parameters.uprating.CPI
    data = {}
    for year in range(2014, 2029):
        data[f"{year + 1}-01-01"] = cpi(instant(f"{year}-09-01"))
    parameters.uprating.add_child("benefits", Parameter("benefits", data=data))
    return parameters