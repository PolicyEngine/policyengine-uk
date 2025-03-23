from policyengine_core.parameters import (
    ParameterNode,
    Parameter,
    get_parameter,
)

YEARS = list(range(2022, 2035))


def add_triple_lock(parameters: ParameterNode) -> ParameterNode:
    average_earnings = parameters.gov.obr.per_capita.employment_income
    cpi = parameters.gov.obr.consumer_price_index
    min_rate = parameters.gov.dwp.state_pension.triple_lock.minimum_rate

    values = {}

    index = 1

    for year in YEARS:
        earnings_increase = average_earnings(year - 1) / average_earnings(
            year - 2
        )
        cpi_increase = cpi(year - 1) / cpi(year - 2)
        min_rate_y = min_rate(year)
        triple_lock_increase = max(earnings_increase, cpi_increase, min_rate_y)
        index *= triple_lock_increase
        values[f"{year}-01-01"] = round(index, 3)

    new_parameter = Parameter(
        "gov.dwp.state_pension.triple_lock.index",
        data={"values": values, "metadata": {"unit": "/1"}},
    )
    parameters.gov.dwp.state_pension.triple_lock.add_child(
        "index", new_parameter
    )
    return parameters
