"""The lagged economic series track their source rather than a fixed end year.

A parameter carries its final value forward rather than raising, so a lagged
series that stops early does not fail — it silently holds a stale growth rate.
Average earnings are not flat, so that previously left the lagged earnings
index well below the series it lags.
"""

from policyengine_uk import system


def _obr(node: str):
    return getattr(system.parameters.gov.economic_assumptions, node).obr


def _last_year(parameter) -> int:
    return max(int(value.instant_str[:4]) for value in parameter.values_list)


def test_lagged_series_reach_the_end_of_their_source():
    """The lag runs exactly one year past its source, and holds its last value.

    A parameter carries its terminal value forward, so an off-by-one series
    that stopped a year early would still answer correctly at every year
    tested above. Pinning the terminal year and value is what catches it.
    """
    growth = _obr("yoy_growth")

    for source_name, lagged_name in (
        ("consumer_price_index", "lagged_cpi"),
        ("average_earnings", "lagged_average_earnings"),
    ):
        source = getattr(growth, source_name)
        lagged = getattr(growth, lagged_name)
        last_source_year = _last_year(source)

        assert _last_year(lagged) == last_source_year + 1, (
            f"{lagged_name} should end one year after {source_name}"
        )
        assert lagged(str(last_source_year + 1)) == source(str(last_source_year)), (
            f"{lagged_name} does not end on {source_name}'s final value"
        )


def test_lagged_series_hold_the_previous_year_of_their_source():
    growth = _obr("yoy_growth")

    for source_name, lagged_name in (
        ("consumer_price_index", "lagged_cpi"),
        ("average_earnings", "lagged_average_earnings"),
    ):
        source = getattr(growth, source_name)
        lagged = getattr(growth, lagged_name)

        for year in (2030, 2035, 2039):
            assert lagged(str(year)) == source(str(year - 1)), (
                f"{lagged_name} at {year} is not {source_name} at {year - 1}"
            )


def test_the_lagged_earnings_index_keeps_growing_with_earnings():
    """Earnings growth is not flat, so a frozen lag shows up in the index."""
    index = _obr("indices").lagged_average_earnings

    assert index("2039") > index("2035") > index("2030")


def test_lagged_parameter_names_match_their_position_in_the_tree():
    growth = _obr("yoy_growth")

    for lagged_name in ("lagged_cpi", "lagged_average_earnings"):
        lagged = getattr(growth, lagged_name)
        assert lagged.name.endswith(f"yoy_growth.obr.{lagged_name}")
