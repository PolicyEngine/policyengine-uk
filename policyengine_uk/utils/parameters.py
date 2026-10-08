import datetime
from contextlib import contextmanager

from policyengine_core.model_api import *
from policyengine_core import periods


def str_to_instant(s):
    return periods.Instant(tuple(map(lambda s: int(s), s.split("-"))))


def backdate_parameters(root: str = None, first_instant: str = "2021-01-01") -> Reform:
    first_instant = str_to_instant(first_instant)
    node = root
    for param in node.get_descendants():
        if isinstance(param, Parameter):
            earliest = param.values_list[-1]
            earliest_value = earliest.value
            earliest_instant = str_to_instant(earliest.instant_str)
            if first_instant < earliest_instant:
                num_days = (earliest_instant.date - first_instant.date).days
                param.update(
                    period=periods.Period(("day", first_instant, num_days)),
                    value=earliest_value,
                )
    return root


def fiscal_year_average(param, year: int):
    """Day-weighted average of a parameter across a UK fiscal year.

    Returns None where any value in the year is missing or non-numeric, so
    the caller can fall back to sampling a single date.
    """
    start = datetime.date(year, 4, 6)
    end = datetime.date(year + 1, 4, 6)

    changes = []
    for value_at_instant in param.values_list:
        try:
            instant = datetime.date.fromisoformat(value_at_instant.instant_str)
        except ValueError:
            return None
        if start < instant < end:
            changes.append(instant)

    boundaries = [start, *sorted(changes), end]
    total = 0.0
    for segment_start, segment_end in zip(boundaries, boundaries[1:]):
        value = param(segment_start.isoformat())
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None
        total += value * (segment_end - segment_start).days

    return total / (end - start).days


def uk_fiscal_year_period(time_period):
    """Translate a bare year into the UK fiscal year it names.

    A UK parameter change for "2025" means the fiscal year starting 6 April
    2025. Writing it as the calendar year leaves January to April of 2026
    on prior law, which fiscal-year conversion then blends into the value —
    an annual override of 0.5 came out as 0.42. Non-year periods pass
    through untouched.
    """
    year = None
    if isinstance(time_period, int):
        year = time_period
    elif isinstance(time_period, str) and time_period.strip().isdigit():
        year = int(time_period.strip())
    if year is None or not 1900 < year < 2200:
        return time_period
    start = periods.Instant((year, 4, 6))
    days = (datetime.date(year + 1, 4, 6) - datetime.date(year, 4, 6)).days
    return periods.Period(("day", start, days))


def convert_to_fiscal_year_parameters(parameters):
    """
    Convert parameters to use UK fiscal year values.

    The UK fiscal year runs April 6 to April 5. When querying a parameter
    for a year (e.g., param("2026")), we want the value at April 30 of
    that year (which represents the fiscal year starting April 6).

    This function samples each parameter at April 30 of each year and
    sets that as the value for the entire year period.

    Sampling a single date drops any change taking effect later in the fiscal
    year. Parameters carrying `fiscal_year_blend: true` in their metadata are
    day-weighted across the year instead, which is the right annualisation for
    a rate or threshold that applies to a flow spread over the year. Leave the
    flag off where the value at a point in time is what applies, as for a tax
    charged on a transaction at the rate in force on its date.

    Parameters with ``preserve_calendar_dates: true`` retain statutory dates.
    Their formulas must explicitly annualise the underlying transactions.

    Values are computed for every year before any are written, so that
    rewriting one year cannot affect the reading of another.
    """
    for param in parameters.get_descendants():
        if isinstance(param, Parameter):
            if (param.metadata or {}).get("preserve_calendar_dates", False):
                continue
            blend = (param.metadata or {}).get("fiscal_year_blend", False)
            _write_model_year_values(param, param, blend)
    return parameters


# Cover years from 2015 through 2040 for long-term projections
FISCAL_YEARS = list(range(2015, 2041))


def _write_model_year_values(param, schedule, blend: bool) -> None:
    """Write one value per model year to param, read from a dated schedule."""
    values = {}
    for year in FISCAL_YEARS:
        value = fiscal_year_average(schedule, year) if blend else None
        if value is None:
            value = schedule(f"{year}-04-30")
        values[year] = value
    for year, value in values.items():
        param.update(
            period=f"{year}",
            value=value,
        )


def _is_blended(param) -> bool:
    metadata = param.metadata or {}
    return bool(metadata.get("fiscal_year_blend")) and not metadata.get(
        "preserve_calendar_dates"
    )


class _DetachedParent:
    """Parent for a working copy of a dated schedule.

    ``Parameter.update`` clears and marks its parent; a copy hanging off the
    baseline tree would otherwise mark the baseline as modified.
    """

    def clear_parent_cache(self):
        pass

    def mark_as_modified(self):
        pass


def _to_instant(value):
    if value is None or isinstance(value, periods.Instant):
        return value
    return periods.instant(value)


def _dated_update(value, period, start, stop, remove_after):
    """Restate an update to the model-year tree as one to the dated schedule.

    On the converted tree a calendar year holds the model year that starts in
    it, so 1 January is a model-year boundary there, and so is the day after
    31 December. Those boundaries move to 6 April on the dated schedule. Any
    other date is kept as written. Returns the update and whether every
    boundary was a model-year boundary.
    """
    if period is not None:
        if isinstance(period, str):
            period = periods.period(period)
        start, stop = period.start, period.stop
    start, stop = _to_instant(start), _to_instant(stop)
    aligned = True
    if start is not None and start.year > 1:
        if (start.month, start.day) == (1, 1):
            start = periods.Instant((start.year, 4, 6))
        else:
            aligned = False
    if stop is not None:
        following = stop.offset(1, "day")
        if (following.month, following.day) == (1, 1):
            stop = periods.Instant((following.year, 4, 5))
        else:
            aligned = False
    return (
        dict(value=value, start=start, stop=stop, remove_after=remove_after),
        aligned,
    )


def _reblend(param, updates, baseline) -> None:
    """Re-run the fiscal-year average after a reform edits a blended parameter.

    The reform's updates are replayed on the dated schedule the model-year
    values were averaged from: the uprated baseline, or the schedule left by
    an earlier reform. Model years are rewritten only if some update starts
    or ends part-way through a year, so whole-year reforms keep their current
    values exactly.
    """
    source = param.__dict__.get("_fiscal_year_dated_schedule")
    if source is None:
        source = baseline.get_child(param.name)
    schedule = source.clone()
    schedule.parent = _DetachedParent()
    part_year = False
    for update in updates:
        kwargs, aligned = _dated_update(**update)
        schedule.update(**kwargs)
        part_year = part_year or not aligned
    param.__dict__["_fiscal_year_dated_schedule"] = schedule
    if part_year:
        _write_model_year_values(param, schedule, blend=True)


@contextmanager
def reblend_dated_reforms(tax_benefit_system):
    """Day-weight reforms dated part-way through a year on blended parameters.

    Reforms edit the converted tree, where each blended parameter
    (``fiscal_year_blend: true``) already holds a day-weighted average per
    model year. A change dated, say, 1 September would otherwise apply only
    from the September monthly reading and leave the earlier months on an
    average that still includes the rates the reform replaces. Inside this
    context each update to a blended parameter is recorded, and on exit it
    is replayed on the dated schedule and the affected parameter re-averaged.
    """
    parameters = tax_benefit_system.parameters
    gov = parameters.children.get("gov")
    baseline = parameters.children.get("baseline")
    if gov is None or baseline is None:
        yield
        return
    recorded = {}
    wrapped = []
    for param in gov.get_descendants():
        if (
            not isinstance(param, Parameter)
            or not _is_blended(param)
            or "update" in param.__dict__
        ):
            continue

        def record(
            value=None,
            period=None,
            start=None,
            stop=None,
            remove_after=False,
            _param=param,
            _update=param.update,
        ):
            result = _update(
                value=value,
                period=period,
                start=start,
                stop=stop,
                remove_after=remove_after,
            )
            recorded.setdefault(id(_param), (_param, []))[1].append(
                dict(
                    value=value,
                    period=period,
                    start=start,
                    stop=stop,
                    remove_after=remove_after,
                )
            )
            return result

        param.update = record
        wrapped.append(param)
    try:
        yield
    finally:
        for param in wrapped:
            del param.__dict__["update"]
    for param, updates in recorded.values():
        _reblend(param, updates, baseline)
    if recorded:
        tax_benefit_system.reset_parameter_caches()


_STATE_PENSION_AGE_REPLACEMENT = (
    "State Pension age now follows the statutory timetable by date of birth "
    "(Pensions Act 1995 Sch 4 para 1). Change the rows of "
    "gov.dwp.state_pension.age.age_by_birth_date (the age, in months) or "
    "gov.dwp.state_pension.age.day_by_birth_date (the day) for the births you "
    "want to change, for example gov.dwp.state_pension.age.age_by_birth_date[14]"
    ".amount for people born from 6 March 1961 until the next bracket, or "
    "gov.dwp.state_pension.age.male.age for men born before 6 December 1953. "
    "Read a person's State Pension age from the state_pension_age or is_SP_age "
    "variables."
)

# Parameters removed from the tree, with what replaces them, so a reform or
# saved policy that still names one fails with directions instead of a bare
# lookup error.
REMOVED_PARAMETERS = {
    "gov.dwp.state_pension.age.male": _STATE_PENSION_AGE_REPLACEMENT,
    "gov.dwp.state_pension.age.female": _STATE_PENSION_AGE_REPLACEMENT,
}


def check_parameter_not_removed(path: str) -> None:
    """Raise a ValueError naming the replacement if path was removed."""
    if path in REMOVED_PARAMETERS:
        raise ValueError(
            f"The parameter {path} has been removed. {REMOVED_PARAMETERS[path]}"
        )


class RemovedParameterNode(ParameterNode):
    """Keep a removed path discoverable without accepting scalar reforms.

    Male State Pension age still has valid children, so the compatibility
    node must support normal tree traversal and cloning. API reform code
    reads values_list before updating; both operations give migration help.
    """

    @property
    def values_list(self):
        check_parameter_not_removed(self.name)

    def update(self, *args, **kwargs):
        check_parameter_not_removed(self.name)


class RemovedParameterRoot(ParameterNode):
    """Reject explicit lookups of removed scalars, including empty policies."""

    def get_child(self, path: str):
        check_parameter_not_removed(path)
        return super().get_child(path)


def add_removed_parameter_aliases(parameters: ParameterNode) -> ParameterNode:
    if not isinstance(parameters, RemovedParameterRoot):
        root = RemovedParameterRoot(parameters.name, data={})
        root.__dict__ = parameters.__dict__.copy()
        for child in root.children.values():
            child.parent = root
        parameters = root
    age = parameters.gov.dwp.state_pension.age
    for path, replacement in REMOVED_PARAMETERS.items():
        name = path.rsplit(".", 1)[1]
        previous = age.children.get(name)
        if isinstance(previous, RemovedParameterNode):
            continue
        alias = RemovedParameterNode(path, data={})
        if previous is not None:
            alias.metadata.update(previous.metadata)
            for child_name, child in previous.children.items():
                alias.add_child(child_name, child)
        alias.description = f"The parameter {path} has been removed. {replacement}"
        alias.metadata.update(
            label=f"removed {name} State Pension age parameter",
            removed=True,
            economy=False,
            household=False,
        )
        age.children[name] = alias
        setattr(age, name, alias)
        alias.parent = age
    return parameters
