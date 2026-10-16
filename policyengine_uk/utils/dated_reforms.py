"""Apply dated parameter changes to the statutory timeline.

A parameter's YAML holds its statutory values at their legal dates.
Processing (``CountryTaxBenefitSystem.process_parameters``) projects them
forward: uprating, income tax and NICs threshold indexation, the triple lock
and the other generated series. It then annualises each parameter to UK
fiscal years by its documented rule: the value at 30 April, the day-weighted
average for ``fiscal_year_blend`` parameters, or the statutory dates
themselves for ``preserve_calendar_dates`` parameters.

Every reform route writes its changes onto the statutory timeline and then
runs that same processing. So a reform is uprated, indexed and annualised as
current law is: a rate change from 6 April 2027 sets fiscal year 2027, a
change to the personal allowance after 2030-31 moves the aligned NICs
thresholds, and a change to a September CPI forecast moves every threshold
indexed by it. Editing the already-annualised parameters instead, as the
reform-dict routes used to, kept a change dated 6 April out of that fiscal
year (its 30 April value had already been taken) and left derived
parameters on the baseline.

Prior law after a bounded change
--------------------------------

Outside ``[start, stop]`` a change leaves prior law in force:

- where the timeline states values, they apply on their dates, and the
  value in force at ``stop`` resumes the day after it;
- where it states none (the parameter's future is projected by uprating or
  indexation), prior law's projected path applies: the values the parameter
  takes with every other change in the reform but without its own. That
  covers both the years between the last stated value and a change that
  starts after it, and the years after a bounded change.

``Parameter.update`` instead restores the last stated value as a new stated
value, so a one-year change to an uprated parameter froze the next year at
that value (a UC standard allowance change for 2027-28 gave £424.90 in
2028-29 instead of the uprated amount) and every later year was uprated from
it. Whether a statutory amount changed for some years should instead let
indexation resume from the changed amount, as Income Tax Act 2007 s57 does
from "the previous tax year", is a separate contract choice; see
``policyengine_uk.reform_contract``.

How each route reads its period keys
------------------------------------

The routes keep the readings they documented before, except on the
calendar-year series (starred, and below):

=====================  ========================  =========================  ==========================
Key                    reform dict               ``parameter_changes``      ``Reform.from_dict``
=====================  ========================  =========================  ==========================
``"start.stop"``       ``[start, stop]``         ``[start, stop]``          ``[start, stop]``
``"2027"`` or 2027     fiscal year 2027 only*    fiscal year 2027 only*     from 1 January 2027 on
``"2027-04-06"``       one day of the            that one day               from that day on
                       annualised parameter
``"year:2027:2"``      calendar years 2027-28    calendar years 2027-28     calendar years 2027-28
``"ETERNITY"``         not accepted              not accepted               all time
scalar                 from 1 January 2023 on    2000 to 2099               2000 to 2099
=====================  ========================  =========================  ==========================

Starred: calendar year 2027 on a calendar-year series (below), where a
``"2027-01-01"`` key also names calendar year 2027.

"From ... on" holds the value flat to 31 December 2100, as editing the
annualised parameters did; uprating and indexation do not apply to it.

Calendar-year series
--------------------

Some parameters hold one value per calendar year, dated 1 January, and are
read there: the parameters outside ``gov``, which are never annualised and
which formulas read at 1 January, and the parameters carrying
``calendar_year_series`` metadata, on themselves or an ancestor node (the
growth rates in ``gov.economic_assumptions.yoy_growth`` and the indices
processing builds from them). Processing reads the growth rates at
1 January: the indices, the forecasts of the statutory uprating inputs, the
lagged series and the dataset uprating all do. On these parameters the
reform dict and ``parameter_changes`` read a bare year, and a key naming
its 1 January (``"2027-01-01"``), as that calendar year, 1 January to
31 December. The fiscal year from 6 April would reach the next year's value
instead: a 2027 earnings growth rate keyed ``"2027"`` showed as 2027's but
moved the 2028 index, the May to July 2028 earnings input and the April
2029 triple lock.

Generated series
----------------

Processing generates some parameters from others: the triple lock rate
(``gov.economic_assumptions.yoy_growth.triple_lock``), the lagged and
private pension series, the September CPI uprating rate and every index
under ``gov.economic_assumptions.indices``. A change to one is written onto
its timeline just after the step that generates it, so the steps after it,
and uprating, use it: a triple lock rate set for April 2028 uprates the
State Pension, and a changed index uprates whatever is uprated by it.
Each route reads its keys as for the statutory parameters. The deprecated
labour supply aliases (``gov.simulation.labor_supply_responses.*``) are
copies of ``gov.simulation.labour_supply_responses.*``; a change to one is
made to the parameter it copies.

Legacy overrides
----------------

A reform-dict key naming a single day or month keeps its legacy meaning: it
overrides the annualised parameter on that day or month only, after
processing. Formulas read an annual parameter at 1 January, so a
``"2027-01-01"`` key sets fiscal year 2027 and a ``"2027-04-06"`` key changes
nothing; ``ReformPeriodWarning`` says so. Use ``"2027-04-06.2100-12-31"``
for a change from 6 April 2027. A reform-dict path that is neither in the
statutory tree nor generated by processing (one added by a structural
reform) is also applied to the annualised parameters, after the structural
reforms that come before it. Changes to the
annualised parameters always follow the statutory-timeline changes, so a
reform-dict parameter that mixes single-day keys with other keys gets the
single-day keys last, whatever their order (``ReformPeriodWarning`` says
so), and a structural reform class that edits a parameter overrides a dict
change to it even when the dict comes later in a tuple.

The tax-benefit system keeps every dated change and legacy override it has
been given. Any later rebuild of its parameters (another call to
``Simulation.apply_parameter_changes``, or a modifier that reloads and
reprocesses the parameters, as ``no_economic_assumptions`` does) writes them
all again, onto the parameters as that modifier left them. Nodes a
structural reform added to the processed parameters (a new parameter, or a
band appended to a scale) are added back (``graft_missing_nodes``); other
edits made directly to existing processed parameters are not kept.

``Scenario.apply`` on an already-built simulation never rebuilds: it edits
the annualised parameters, as it always has, so every change it makes is a
legacy override and dated keys are not annualised again.
"""

from __future__ import annotations

import datetime
import warnings
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from policyengine_core.parameters import Parameter, ParameterNode, ParameterScale
from policyengine_core.parameters.parameter_at_instant import ParameterAtInstant
from policyengine_core.periods import Instant, Period, instant, period

from policyengine_uk.utils.parameters import (
    BACKDATED_VALUE,
    check_parameter_not_removed,
)

# A change "from a date on" holds to the end of this day, as editing the
# annualised parameters held it indefinitely within the model's horizon.
FLAT_STOP = instant("2100-12-31")
# Where the reform dict's scalar shorthand starts (unchanged).
REFORM_DICT_SCALAR_START = instant("2023-01-01")
# policyengine-core's scalar window, ``year:2000:100``.
CORE_SCALAR_PERIOD = "year:2000:100"
EARLIEST = Instant((1, 1, 1))
# Where process_parameter_tree backdates each parameter's first value to.
BACKDATED_FROM = "2015-01-01"

# Metadata marking a node or parameter whose values are for calendar years.
CALENDAR_YEAR_SERIES = "calendar_year_series"

REFORM_DICT = "reform_dict"
PARAMETER_CHANGES = "parameter_changes"
REFORM_FROM_DICT = "reform_from_dict"
# Scenario.apply's parameter_changes on a built simulation: every period.
ALL_PERIODS = "all_periods"
READINGS = (REFORM_DICT, PARAMETER_CHANGES, REFORM_FROM_DICT)


class ReformPeriodWarning(UserWarning):
    """A reform period key that is unlikely to mean what was intended."""


@dataclass(frozen=True)
class ParameterAssignment:
    """A value in force over ``[start, stop]`` on the statutory timeline.

    Both ends are inclusive. ``order`` is the position at which the change
    is written: a later change wins where two overlap.
    """

    path: str
    start: Instant
    stop: Instant
    value: Any
    order: int = 0


@dataclass(frozen=True)
class LegacyOverride:
    """A change applied to the annualised parameters, as the route used to.

    ``key`` is the route's own period key (None for a scalar) and
    ``reading`` the route that gave it.
    """

    path: str
    key: Any
    value: Any
    reading: str = REFORM_DICT


def uk_fiscal_year_bounds(year: int) -> Tuple[Instant, Instant]:
    """6 April of ``year`` to 5 April of the next year."""
    return instant(f"{year}-04-06"), instant(f"{year + 1}-04-05")


def calendar_year_bounds(year: int) -> Tuple[Instant, Instant]:
    """1 January to 31 December of ``year``."""
    return instant(f"{year}-01-01"), instant(f"{year}-12-31")


def new_year_day(key: str) -> Optional[int]:
    """The year of a key naming 1 January of one year (``"2027-01-01"``)."""
    try:
        parsed: Period = period(key)
    except Exception:
        return None
    if parsed.unit != "day" or parsed.size != 1:
        return None
    start = parsed.start
    return start.year if (start.month, start.day) == (1, 1) else None


def named_year(
    key: Any, path: str, calendar_years: Optional[Callable[[str], bool]]
) -> Optional[Tuple[Instant, Instant]]:
    """The year a key names, as the bounds a change keyed by it covers.

    A bare year names the UK fiscal year from 6 April, except on a
    parameter whose values are for calendar years (``calendar_years(path)``):
    there it, or a key naming its 1 January, names that calendar year.
    """
    calendar = calendar_years is not None and calendar_years(path)
    year = bare_year(key)
    if year is not None:
        return calendar_year_bounds(year) if calendar else uk_fiscal_year_bounds(year)
    if calendar and isinstance(key, str):
        year = new_year_day(key)
        if year is not None:
            return calendar_year_bounds(year)
    return None


def bare_year(key: Any) -> Optional[int]:
    """The year a bare-year key names, or None."""
    if isinstance(key, bool):
        return None
    if isinstance(key, int):
        year = key
    elif isinstance(key, str) and key.strip().isdigit():
        year = int(key.strip())
    else:
        return None
    return year if 1900 < year < 2200 else None


def interval_bounds(key: str) -> Tuple[Instant, Instant]:
    start, separator, stop = key.partition(".")
    if not separator or "." in stop:
        raise ValueError(f"Expected a 'start.stop' period key; got '{key}'.")
    start_instant, stop_instant = instant(start), instant(stop)
    if stop_instant < start_instant:
        raise ValueError(f"Period key '{key}' ends before it starts.")
    return start_instant, stop_instant


def period_bounds(key: str) -> Tuple[Instant, Instant]:
    parsed = period(key)
    return parsed.start, parsed.stop


def is_sub_year(key: str) -> bool:
    """Whether a key names one day or month (a legacy reform-dict key)."""
    parsed: Period = period(key)
    return parsed.unit in ("day", "month") and parsed.size == 1


def _check_path(path: str) -> None:
    check_parameter_not_removed(path)


def read_reform_dict(
    reform: Mapping[str, Any],
    defines: Callable[[str], bool],
    order_start: int = 0,
    warn: bool = False,
    calendar_years: Optional[Callable[[str], bool]] = None,
) -> Tuple[List[ParameterAssignment], List[LegacyOverride]]:
    """Read a ``Simulation(reform=dict)`` / ``Scenario.from_reform`` dict.

    ``defines(path)`` says whether a path is written on the statutory
    timeline: the statutory parameter tree defines it, or processing
    generates it (then the change is written just after it is generated).
    Changes to other paths, and single-day or single-month keys, are
    returned as legacy overrides of the annualised parameters; ``warn``
    warns about single-day keys that change no annual value.
    ``calendar_years(path)`` says whether a parameter's values are for
    calendar years, so that a bare year, or a key naming its 1 January,
    names that calendar year (see ``named_year``).
    """
    assignments: List[ParameterAssignment] = []
    legacy: List[LegacyOverride] = []
    order = order_start
    for path, spec in reform.items():
        _check_path(path)
        statutory = defines(path)
        if not isinstance(spec, Mapping):
            if statutory:
                assignments.append(
                    ParameterAssignment(
                        path, REFORM_DICT_SCALAR_START, FLAT_STOP, spec, order
                    )
                )
                order += 1
            else:
                legacy.append(LegacyOverride(path, None, spec))
            continue
        for key, value in spec.items():
            text = str(key)
            year = named_year(key, path, calendar_years if statutory else None)
            if "." in text:
                start, stop = interval_bounds(text)
            elif year is not None:
                start, stop = year
            elif is_sub_year(text):
                if warn:
                    _warn_sub_year_key(
                        path,
                        text,
                        calendar_years is not None and calendar_years(path),
                    )
                legacy.append(LegacyOverride(path, text, value))
                continue
            else:
                start, stop = period_bounds(text)
            if statutory:
                assignments.append(ParameterAssignment(path, start, stop, value, order))
                order += 1
            else:
                legacy.append(LegacyOverride(path, text, value))
    if warn:
        mixed = sorted(
            {override.path for override in legacy}
            & {assignment.path for assignment in assignments}
        )
        for path in mixed:
            _warn(
                f"Reform for {path} mixes single-day keys with other keys. The "
                "single-day keys apply to the annualised parameter after the "
                "others, whatever their order in the dict."
            )
    return assignments, legacy


def _warn(message: str) -> None:
    warnings.warn(message, ReformPeriodWarning, stacklevel=4)


def _warn_sub_year_key(path: str, key: str, calendar: bool = False) -> None:
    parsed = period(key)
    if parsed.unit == "day" and str(parsed.start)[5:] == "01-01":
        return
    kind = "calendar" if calendar else "fiscal"
    _warn(
        f"Reform key '{key}' for {path} overrides the annualised parameter on "
        f"that {parsed.unit} only, and formulas read annual parameters at "
        f"1 January, so it may change nothing. For a change from that date "
        f"use '{parsed.start}.{FLAT_STOP}'; for one {kind} year use the bare "
        "year."
    )


def read_parameter_changes(
    changes: Mapping[str, Any],
    order_start: int = 0,
    calendar_years: Optional[Callable[[str], bool]] = None,
) -> List[ParameterAssignment]:
    """Read ``Scenario(parameter_changes=...)``.

    ``calendar_years`` is as for ``read_reform_dict``.
    """
    assignments: List[ParameterAssignment] = []
    order = order_start
    for path, spec in changes.items():
        _check_path(path)
        if not isinstance(spec, Mapping):
            start, stop = period_bounds(CORE_SCALAR_PERIOD)
            assignments.append(ParameterAssignment(path, start, stop, spec, order))
            order += 1
            continue
        for key, value in spec.items():
            text = str(key)
            year = named_year(key, path, calendar_years)
            if "." in text:
                start, stop = interval_bounds(text)
            elif year is not None:
                start, stop = year
            else:
                start, stop = period_bounds(text)
            assignments.append(ParameterAssignment(path, start, stop, value, order))
            order += 1
    return assignments


def read_reform_from_dict(
    parameter_values: Mapping[str, Any],
    defines: Callable[[str], bool],
    order_start: int = 0,
) -> Tuple[List[ParameterAssignment], List[LegacyOverride]]:
    """Read the dict behind a policyengine-core ``Reform.from_dict`` class.

    Follows policyengine-core's documented key reading. Within a parameter,
    changes apply in ascending start order, as policyengine-core applies
    them.
    """
    assignments: List[ParameterAssignment] = []
    legacy: List[LegacyOverride] = []
    order = order_start
    for path, spec in parameter_values.items():
        _check_path(path)
        if not defines(path):
            if isinstance(spec, Mapping):
                legacy.extend(
                    LegacyOverride(path, str(key), value, REFORM_FROM_DICT)
                    for key, value in spec.items()
                )
            else:
                legacy.append(LegacyOverride(path, None, spec, REFORM_FROM_DICT))
            continue
        entries: List[Tuple[Instant, Instant, Any]] = []
        if not isinstance(spec, Mapping):
            start, stop = period_bounds(CORE_SCALAR_PERIOD)
            entries.append((start, stop, spec))
        else:
            for key, value in spec.items():
                text = str(key)
                if text == "ETERNITY":
                    start, stop = EARLIEST, FLAT_STOP
                elif "." in text:
                    start, stop = interval_bounds(text)
                elif ":" in text:
                    start, stop = period_bounds(text)
                else:
                    start, stop = instant(text), FLAT_STOP
                entries.append((start, stop, value))
        entries.sort(key=lambda entry: entry[0])
        for start, stop, value in entries:
            assignments.append(ParameterAssignment(path, start, stop, value, order))
            order += 1
    return assignments, legacy


def apply_legacy_overrides(
    parameters: ParameterNode, overrides: Iterable[LegacyOverride]
) -> None:
    """Apply changes to the annualised parameters, as each route used to."""
    from policyengine_core.reforms.reform import _period_key_update_kwargs

    from policyengine_uk.utils.parameters import uk_fiscal_year_period

    for override in overrides:
        target = parameters.get_child(override.path)
        if override.reading == ALL_PERIODS:
            target.update(period=None, value=override.value)
        elif override.reading == REFORM_FROM_DICT:
            if override.key is None:
                target.update(period=CORE_SCALAR_PERIOD, value=override.value)
            else:
                target.update(**_period_key_update_kwargs(override.key, override.value))
        elif override.key is None:
            target.update(
                start=REFORM_DICT_SCALAR_START, stop=None, value=override.value
            )
        elif "." in override.key:
            start, stop = interval_bounds(override.key)
            target.update(start=start, stop=stop, value=override.value)
        else:
            target.update(
                period=(
                    uk_fiscal_year_period(override.key)
                    if target.metadata.get("preserve_calendar_dates")
                    else period(override.key)
                ),
                value=override.value,
            )


Timeline = List[ParameterAtInstant]


def _entry(name: str, instant_str: str, value: Any) -> ParameterAtInstant:
    return ParameterAtInstant(name, instant_str, data={"value": value})


def _value_in_force(values: Timeline, instant_str: str) -> Any:
    """The value of a descending timeline at an instant (None before it)."""
    for entry in values:
        if entry.instant_str <= instant_str:
            return entry.value
    return None


def _last_stated(values: Timeline) -> Optional[str]:
    return max((entry.instant_str for entry in values), default=None)


def requires_projection(parameter: Parameter, assignment: ParameterAssignment) -> bool:
    """Whether a change reaches the part of the timeline projection fills.

    That is a change starting after the parameter's last stated value, whose
    prior law before it is projected, or a bounded change with no stated
    value after it, whose prior law after it is projected.
    """
    last = _last_stated(parameter.values_list)
    if last is None:
        return False
    if str(assignment.start) > last:
        return True
    return assignment.stop < FLAT_STOP and str(assignment.stop) >= last


def write_assignment(
    parameter: Parameter,
    assignment: ParameterAssignment,
    projected: Optional[Callable[[str], Optional[Timeline]]] = None,
) -> None:
    """Write a change onto a parameter's statutory timeline.

    A change starting on or before the parameter's first stated value
    records that value (``BACKDATED_VALUE``) for processing to backdate to
    ``BACKDATED_FROM`` instead of the change's. Where the change reaches past
    the parameter's last stated value (see ``requires_projection``),
    ``projected(name)`` supplies prior law's
    projected timeline, whose values after the last stated one are first
    written in as stated values: uprating and indexation extend a timeline
    only from its last stated value, so without them the years between that
    value and the change, or after a bounded change, would lose their
    projection. Then, as ``Parameter.update`` does, entries within the
    change are replaced by its value and the value in force at ``stop`` is
    restored on the next day unless an entry already starts then. A change
    that ends before the first stated value resumes with that value, as
    processing would backdate it.
    """
    name = parameter.name
    start_str = str(assignment.start)
    stop_str = str(assignment.stop)
    next_str = str(assignment.stop.offset(1, "day"))
    old: Timeline = list(parameter.values_list)
    first = min((entry.instant_str for entry in old), default=None)
    if first is not None and start_str <= first and BACKDATED_FROM < first:
        # Processing backdates a parameter's earliest value to
        # BACKDATED_FROM, after the generation steps. A change starting on or
        # before the first stated value becomes the earliest, so prior law's
        # first value is recorded for processing to backdate instead; kept
        # from the first such change, it stays prior law's when another
        # starts earlier. Writing it at BACKDATED_FROM here would move the
        # first year the generation steps read (an index's base year).
        earliest = min(old, key=lambda entry: entry.instant_str)
        if parameter.metadata is None:
            parameter.metadata = {}
        parameter.metadata.setdefault(BACKDATED_VALUE, earliest.value)
    path = projected(name) if projected is not None else None
    if path is not None and requires_projection(parameter, assignment):
        last = _last_stated(old)
        old += [
            _entry(name, entry.instant_str, entry.value)
            for entry in path
            if entry.instant_str > last
        ]
    old.sort(key=lambda entry: entry.instant_str, reverse=True)
    later = [entry for entry in old if entry.instant_str > stop_str]
    earlier = [entry for entry in old if entry.instant_str < start_str]
    resumed: Timeline = []
    if not later or later[-1].instant_str != next_str:
        in_force = [entry for entry in old if entry.instant_str <= stop_str]
        # Before its first stated value a parameter takes that value, as
        # processing backdates it; resuming with nothing would leave the
        # years up to that value empty. Where an earlier change starting on
        # or before it recorded prior law's first value, that is the value
        # (the first entry is now that change's). A stated null stays null.
        recorded = parameter.metadata or {}
        if in_force:
            resumed_value = in_force[0].value
        elif BACKDATED_VALUE in recorded:
            resumed_value = recorded[BACKDATED_VALUE]
        else:
            resumed_value = later[-1].value if later else None
        resumed.append(_entry(name, next_str, resumed_value))
    values = later + resumed + [_entry(name, start_str, assignment.value)] + earlier
    values.sort(key=lambda entry: entry.instant_str, reverse=True)
    parameter.values_list = values
    if parameter.parent is not None:
        parameter.parent.clear_parent_cache()
    parameter.mark_as_modified()


def snapshot_timelines(node: ParameterNode) -> Dict[str, Timeline]:
    """Each parameter's current timeline, by name, without copying it.

    ``Parameter.update`` replaces a parameter's ``values_list`` rather than
    changing it, so the lists captured here keep these values after later
    updates (fiscal-year annualisation) replace them.
    """
    return {
        parameter.name: parameter.values_list
        for parameter in node.get_descendants()
        if isinstance(parameter, Parameter)
    }


def copy_timelines(timelines: Dict[str, Timeline]) -> Dict[str, Timeline]:
    """Copies of the timelines, sharing no list or entry with any tree."""
    return {
        name: [_entry(name, entry.instant_str, entry.value) for entry in timeline]
        for name, timeline in timelines.items()
    }


def graft_missing_nodes(
    source: ParameterNode, target: ParameterNode, root: bool = True
) -> List[str]:
    """Add to ``target`` copies of the nodes ``source`` has and it lacks.

    A rebuild or a reload starts from the YAML, so nodes a structural
    reform added to the processed parameters (``parameters.add_child``, or
    a bracket appended to a scale) would otherwise be lost. Existing
    parameters are left as ``target`` has them, and the root's ``baseline``
    child, which every processing builds again, is skipped. Added nodes are
    copies of ``source``'s, not processed again. Returns the names of the
    nodes added.
    """
    added = []
    for key, child in source.children.items():
        if root and key == "baseline":
            continue
        existing = target.children.get(key)
        if existing is None:
            target.add_child(key, child.clone())
            added.append(child.name)
        elif isinstance(child, ParameterNode) and isinstance(existing, ParameterNode):
            added += graft_missing_nodes(child, existing, root=False)
        elif isinstance(child, ParameterScale) and isinstance(existing, ParameterScale):
            for bracket, existing_bracket in zip(child.brackets, existing.brackets):
                added += graft_missing_nodes(bracket, existing_bracket, root=False)
            extra = child.brackets[len(existing.brackets) :]
            for bracket in extra:
                copy = bracket.clone()
                copy.parent = existing
                existing.brackets.append(copy)
                added.append(bracket.name)
            if extra:
                existing.clear_parent_cache()
    return added


def tree_defines(parameters: ParameterNode) -> Callable[[str], bool]:
    """``defines(path)``: whether a parameter tree has a leaf at ``path``."""

    def defines(path: str) -> bool:
        try:
            return isinstance(parameters.get_child(path), Parameter)
        except Exception:
            return False

    return defines
