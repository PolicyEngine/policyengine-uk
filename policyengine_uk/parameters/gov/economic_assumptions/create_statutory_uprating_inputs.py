"""Complete the statutory uprating inputs with forecasts.

Two published statistics set the April uprating of the State Pension:

- ``cpi_september``: the CPI 12-month rate in September (ONS D7G7).
- ``awe_total_pay_may_july``: average weekly earnings, total pay, whole
  economy, the three months May to July on a year earlier (ONS KAC3), as
  used in each year's uprating review: the October labour market release,
  with the latest year holding September's first estimate until then.

Each is keyed to its observation month (1 September, 1 July) and carries
``preserve_calendar_dates`` so fiscal-year conversion leaves the dates alone.
The YAML holds the published figures and then a null: from there on, values
are forecasts.

For a year without a published figure, the forecast is calendar-year growth
in the matching series of ``gov.economic_assumptions.yoy_growth.obr`` plus
``forecast_gap``: the OBR's statutory-basis forecast (its September CPI, or
the quarter nearest the statutory period) minus the stored calendar-year
growth, so the baseline reproduces the OBR's figure. The gap is zero after
the EFO horizon, so the forecast falls back to calendar-year growth. A macro
scenario that edits calendar-year growth moves the inputs one for one; a
scenario that sets an input directly replaces the forecast for the years it
covers.
"""

from policyengine_core.parameters import Parameter, ParameterNode

CPI_OBSERVATION_MONTH_DAY = "09-01"
AWE_OBSERVATION_MONTH_DAY = "07-01"

# Statutory input: (calendar-year series in yoy_growth.obr, observation date).
STATUTORY_INPUTS = {
    "cpi_september": ("consumer_price_index", CPI_OBSERVATION_MONTH_DAY),
    "awe_total_pay_may_july": ("average_earnings", AWE_OBSERVATION_MONTH_DAY),
}


def _last_year(parameter: Parameter) -> int:
    return max(
        int(value.instant_str[:4])
        for value in parameter.values_list
        if value.value is not None
    )


def _first_year(parameter: Parameter) -> int:
    return min(int(value.instant_str[:4]) for value in parameter.values_list)


def last_input_year(parameters: ParameterNode) -> int:
    """Last year covered by the calendar-year series behind the inputs."""
    obr = parameters.gov.economic_assumptions.yoy_growth.obr
    return min(
        _last_year(getattr(obr, series)) for series, _ in STATUTORY_INPUTS.values()
    )


def add_statutory_uprating_inputs(parameters: ParameterNode) -> ParameterNode:
    """Fill each input's unpublished years with its forecast.

    Runs after any scenario has edited the raw parameters and before the
    uprating rules read the inputs.
    """
    inputs = parameters.gov.economic_assumptions.statutory_uprating_inputs
    obr = parameters.gov.economic_assumptions.yoy_growth.obr
    end_year = last_input_year(parameters)
    for name, (series, month_day) in STATUTORY_INPUTS.items():
        parameter = getattr(inputs, name)
        gap = getattr(inputs.forecast_gap, name)
        calendar_growth = getattr(obr, series)
        for year in range(_first_year(parameter), end_year + 1):
            observed = f"{year}-{month_day}"
            if parameter(observed) is not None:
                continue
            forecast = float(calendar_growth(f"{year}-01-01")) + float(
                gap(observed) or 0
            )
            parameter.update(period=f"year:{observed}:1", value=forecast)
    return parameters
