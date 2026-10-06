from policyengine_core.parameters import Parameter, ParameterNode


def lag_source_years(source: Parameter, first_year: int) -> range:
    """Years a one-year-lagged copy of ``source`` should be built for.

    The lagged value at year Y is the source value at Y-1, so the series can
    run to one year past the end of the source. Deriving the end this way
    keeps the lagged series in step with the source: a hardcoded end silently
    freezes the lagged value at the last year written, because a parameter
    carries its final value forward rather than raising.
    """
    last_source_year = max(int(value.instant_str[:4]) for value in source.values_list)
    return range(first_year, last_source_year + 2)


def add_lagged_parameter(
    node: ParameterNode,
    source_name: str,
    lagged_name: str,
    first_year: int,
) -> Parameter:
    """Add a one-year-lagged copy of ``source_name`` as a child of ``node``."""
    source = getattr(node, source_name)

    lagged = Parameter(
        f"{node.name}.{lagged_name}",
        data={
            "values": {
                f"{year}-01-01": source(year - 1)
                for year in lag_source_years(source, first_year)
            },
        },
    )

    node.add_child(lagged_name, lagged)
    return lagged
