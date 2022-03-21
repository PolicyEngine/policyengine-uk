from openfisca_core.parameters import ParameterNode, Parameter
from openfisca_core.periods import instant


def add_tax_benefit_uprating(parameters: ParameterNode) -> ParameterNode:
    """Adds the uprating index used to uprate most tax-benefit instruments (September CPI of the previous year)."""
    cpi = parameters.uprating.CPI
    data = {}
    for year in range(2014, 2029):
        data[f"{year + 1}-04-01"] = cpi(instant(f"{year}-09-01"))
    if not hasattr(parameters.uprating, "september_cpi"):
        parameters.uprating.add_child(
            "september_cpi", Parameter("september_cpi", data=data)
        )
    return parameters
