"""Annualise transaction duties over the UK fiscal year."""

from collections.abc import Iterator
from datetime import datetime
from types import SimpleNamespace

from policyengine_core.parameters import Parameter, ParameterNode


def fiscal_year_segments(
    node: ParameterNode, year: int
) -> Iterator[tuple[SimpleNamespace, float]]:
    """Yield (rates, share of year) for a flat preserved rate schedule.

    Consumption is uniform from 6 April to 5 April. Apply nonlinear rules,
    such as cigarette minimum duty, within each segment before averaging.
    Value-level ``effective_time`` metadata supports 6pm Budget-day changes;
    dates supplied by ordinary reforms take effect at midnight.
    """
    start, end = datetime(year, 4, 6), datetime(year + 1, 4, 6)
    changes = {start, end}
    schedules = {}
    for name, parameter in node.children.items():
        if not isinstance(parameter, Parameter):
            raise TypeError("Excise rate schedules must contain only parameter leaves")
        schedule = []
        for value in parameter.values_list:
            time = value.metadata.get("effective_time", "00:00:00")
            instant = datetime.fromisoformat(f"{value.instant_str}T{time}")
            schedule.append((instant, value.value))
            if start < instant < end:
                changes.add(instant)
        schedules[name] = sorted(schedule, reverse=True)
    boundaries = sorted(changes)
    for first, last in zip(boundaries, boundaries[1:]):
        rates = {}
        for name, schedule in schedules.items():
            rates[name] = next(value for instant, value in schedule if instant <= first)
        yield SimpleNamespace(**rates), (last - first) / (end - start)
