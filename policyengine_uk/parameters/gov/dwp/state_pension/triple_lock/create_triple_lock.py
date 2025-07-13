from policyengine_core.parameters import (
    ParameterNode,
    Parameter,
    get_parameter,
)

YEARS = list(range(2022, 2035))


def add_triple_lock(parameters: ParameterNode) -> ParameterNode:
    obr = parameters.gov.economic_assumptions.yoy_growth.obr
    average_earnings = obr.average_earnings
    cpi = obr.consumer_price_index
    triple_lock = parameters.gov.dwp.state_pension.triple_lock
    min_rate = triple_lock.minimum_rate

    values = {}

    for year in YEARS:
        earnings_increase = average_earnings(year - 1)
        cpi_increase = cpi(year - 1)
        min_rate_y = min_rate(year)
        if triple_lock.include_earnings(
            year
        ) and triple_lock.include_inflation(year):
            triple_lock_increase = max(
                earnings_increase, cpi_increase, min_rate_y
            )
        elif triple_lock.include_earnings(year):
            triple_lock_increase = max(earnings_increase, min_rate_y)
        elif triple_lock.include_inflation(year):
            triple_lock_increase = max(cpi_increase, min_rate_y)
        else:
            triple_lock_increase = min_rate_y
        values[f"{year}-01-01"] = round(triple_lock_increase, 3)

    new_parameter = Parameter(
        "gov.economic_assumptions.yoy_growth.triple_lock",
        data={"values": values, "metadata": {"unit": "/1"}},
    )
    parameters.gov.economic_assumptions.yoy_growth.add_child(
        "triple_lock", new_parameter
    )
    return parameters
