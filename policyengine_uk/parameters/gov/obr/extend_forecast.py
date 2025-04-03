from policyengine_core.parameters import (
    ParameterNode,
    Parameter,
    get_parameter,
)

PARAMETERS_TO_EXTEND = [
    "gov.obr.employment_income",
    "gov.obr.mixed_income",
    "gov.obr.non_labour_income",
    "gov.obr.house_prices",
    "gov.obr.consumer_price_index",
    "gov.obr.mortgage_interest",
    "gov.obr.rent",
]

YEARS = list(range(2030, 2035))


def extend_obr_forecast(
    parameters: ParameterNode, lookback: int = 5
) -> ParameterNode:
    for parameter in PARAMETERS_TO_EXTEND:
        # Extend with the the trend from the last 5 years of the forecast.
        parameter: Parameter = get_parameter(parameters, parameter)
        lookback_start_value = parameter(YEARS[0] - lookback)
        lookback_end_value = parameter(YEARS[0] - 1)
        trend = (lookback_end_value - lookback_start_value) / lookback
        for year in YEARS:
            new_value = parameter(year - 1) + trend
            parameter.update(start=year, value=new_value, stop=None)
    return parameters
