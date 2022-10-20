from policyengine_core.parameters import ParameterNode, Parameter
from policyengine_core.periods import instant


def add_tax_benefit_uprating(parameters: ParameterNode) -> ParameterNode:
    """Adds the uprating index used to uprate most tax-benefit instruments (September CPI of the previous year)."""
    cpi = parameters.calibration.uprating.CPI
    data = {}
    for year in range(2000, 2029):
        data[f"{year + 1}-04-01"] = cpi(instant(f"{year}-09-01"))
    new_parameter = Parameter(
        "uprating.september_cpi",
        data={
            "values": data,
            "metadata": {
                "label": "Tax-benefit CPI",
                "unit": "/1",
                "name": "tax_benefit_cpi",
                "description": "CPI of the previous september (percentage of June 2015 levels). This uprates some (not all) tax-benefit parameters automatically.",
            },
        },
    )
    if not hasattr(parameters.calibration.uprating, "september_cpi"):
        parameters.calibration.uprating.add_child(
            "september_cpi",
            new_parameter,
        )
    else:
        parameters.calibration.uprating.september_cpi = new_parameter

    data = {}
    for year in range(2000, 2029):
        data[f"{year}-01-01"] = cpi(instant(f"{year}-01-01"))
    if not hasattr(parameters.calibration.uprating, "january_cpi"):
        parameters.calibration.uprating.add_child(
            "january_cpi",
            Parameter(
                "uprating.january_cpi",
                data={
                    "values": data,
                },
            ),
        )
    return parameters
