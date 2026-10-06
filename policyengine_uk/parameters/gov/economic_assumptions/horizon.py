from policyengine_core.parameters import Parameter, ParameterNode


def last_year(parameter: Parameter) -> int:
    """The latest year in which ``parameter`` has a dated value."""
    return max(int(value.instant_str[:4]) for value in parameter.values_list)


def growth_horizon(yoy_growth: ParameterNode) -> int:
    """The last year any year-on-year growth series covers.

    The cumulative indices run to this year, and so does every parameter
    uprated by one. Taking it from the series rather than fixing it keeps the
    two in step: a parameter carries its final value forward rather than
    raising, so an index that stopped early would silently freeze everything
    uprated by it from that year on.

    Called once the lagged series are in place, this includes the year they
    run past their source (see ``lagged_series.lag_source_years``).
    """
    return max(
        last_year(parameter)
        for parameter in yoy_growth.get_descendants()
        if isinstance(parameter, Parameter)
    )
