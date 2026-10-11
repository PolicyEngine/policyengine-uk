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

A change over ``[start, stop]`` restores prior law from the day after
``stop``:

- where the timeline states later values, the value in force at ``stop``
  resumes and the later values apply on their dates;
- where it states none (the parameter's future is projected by uprating or
  indexation), prior law's projected path resumes: the values the parameter
  takes, with every other change in the reform, without its own changes.

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

The routes keep the readings they documented before:

=====================  ========================  =========================  ==========================
Key                    reform dict               ``parameter_changes``      ``Reform.from_dict``
=====================  ========================  =========================  ==========================
``"start.stop"``       ``[start, stop]``         ``[start, stop]``          ``[start, stop]``
``"2027"`` or 2027     fiscal year 2027 only     fiscal year 2027 only      from 1 January 2027 on
``"2027-04-06"``       one day of the            that one day               from that day on
                       annualised parameter
``"year:2027:2"``      calendar years 2027-28    calendar years 2027-28     calendar years 2027-28
``"ETERNITY"``         not accepted              not accepted               all time
scalar                 from 1 January 2023 on    2000 to 2099               2000 to 2099
=====================  ========================  =========================  ==========================

"From ... on" holds the value flat to 31 December 2100, as editing the
annualised parameters did; uprating and indexation do not apply to it.

A reform-dict key naming a single day or month keeps its legacy meaning: it
overrides the annualised parameter on that day or month only, after
processing. Formulas read an annual parameter at 1 January, so a
``"2027-01-01"`` key sets fiscal year 2027 and a ``"2027-04-06"`` key changes
nothing; ``ReformPeriodWarning`` says so. Use ``"2027-04-06.2100-12-31"``
for a change from 6 April 2027. A reform-dict path the statutory tree does
not define (one added by a structural reform, or a generated series such as
``gov.economic_assumptions.indices.*``) is also applied to the annualised
parameters, after the structural reforms that come before it.
"""

from __future__ import annotations

import datetime
import warnings
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from policyengine_core.parameters import Parameter, ParameterNode
from policyengine_core.parameters.parameter_at_instant import ParameterAtInstant
from policyengine_core.periods import Instant, Period, instant, period

from policyengine_uk.utils.parameters import check_parameter_not_removed

# A change "from a date on" holds to the end of this day, as editing the
# annualised parameters held it indefinitely within the model's horizon.
FLAT_STOP = instant("2100-12-31")
# Where the reform dict's scalar shorthand starts (unchanged).
REFORM_DICT_SCALAR_START = instant("2023-01-01")
# policyengine-core's scalar window, ``year:2000:100``.
CORE_SCALAR_PERIOD = "year:2000:100"
EARLIEST = Instant((1, 1, 1))

REFORM_DICT = "reform_dict"
PARAMETER_CHANGES = "parameter_changes"
REFORM_FROM_DICT = "reform_from_dict"
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
) -> Tuple[List[ParameterAssignment], List[LegacyOverride]]:
    """Read a ``Simulation(reform=dict)`` / ``Scenario.from_reform`` dict.

    ``defines(path)`` says whether the statutory parameter tree defines a
    path. Changes to paths it does not define, and single-day or single-month
    keys, are returned as legacy overrides of the annualised parameters;
    ``warn`` warns about single-day keys that change no annual value.
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
            year = bare_year(key)
            if "." in text:
                start, stop = interval_bounds(text)
            elif year is not None:
                start, stop = uk_fiscal_year_bounds(year)
            elif is_sub_year(text):
                if warn:
                    _warn_sub_year_key(path, text)
                legacy.append(LegacyOverride(path, text, value))
                continue
            else:
                start, stop = period_bounds(text)
            if statutory:
                assignments.append(ParameterAssignment(path, start, stop, value, order))
                order += 1
            else:
                legacy.append(LegacyOverride(path, text, value))
    return assignments, legacy


def _warn_sub_year_key(path: str, key: str) -> None:
    parsed = period(key)
    if parsed.unit == "day" and str(parsed.start)[5:] == "01-01":
        return
    warnings.warn(
        f"Reform key '{key}' for {path} overrides the annualised parameter on "
        f"that {parsed.unit} only, and formulas read annual parameters at "
        f"1 January, so it may change nothing. For a change from that date "
        f"use '{parsed.start}.{FLAT_STOP}'; for one fiscal year use the bare "
        "year.",
        ReformPeriodWarning,
        stacklevel=4,
    )


def read_parameter_changes(
    changes: Mapping[str, Any], order_start: int = 0
) -> List[ParameterAssignment]:
    """Read ``Scenario(parameter_changes=...)``."""
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
            year = bare_year(key)
            if "." in text:
                start, stop = interval_bounds(text)
            elif year is not None:
                start, stop = uk_fiscal_year_bounds(year)
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
        if override.reading == REFORM_FROM_DICT:
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


def requires_projection(parameter: Parameter, assignment: ParameterAssignment) -> bool:
    """Whether prior law after the change comes from the projected path."""
    if assignment.stop >= FLAT_STOP:
        return False
    stop_str = str(assignment.stop)
    return not any(entry.instant_str > stop_str for entry in parameter.values_list)


def write_assignment(
    parameter: Parameter,
    assignment: ParameterAssignment,
    projected: Optional[Callable[[str], Optional[Timeline]]] = None,
) -> None:
    """Write a change onto a parameter's statutory timeline.

    Entries before ``start`` are kept and entries within the change are
    replaced by its value. After ``stop``: stated later entries are kept,
    with the value in force at ``stop`` restored on the next day unless an
    entry already starts then; with no later entry, ``projected(name)``
    supplies prior law's projected timeline, whose entries after ``stop``
    are copied (with its value on the next day). Without a projection the
    value in force at ``stop`` is restored, as ``Parameter.update`` does.
    """
    name = parameter.name
    start_str = str(assignment.start)
    stop_str = str(assignment.stop)
    next_str = str(assignment.stop.offset(1, "day"))
    old: Timeline = sorted(
        parameter.values_list, key=lambda entry: entry.instant_str, reverse=True
    )
    later = [entry for entry in old if entry.instant_str > stop_str]
    earlier = [entry for entry in old if entry.instant_str < start_str]
    resumed: Timeline = []
    if assignment.stop < FLAT_STOP or later:
        if later:
            if later[-1].instant_str != next_str:
                resumed.append(_entry(name, next_str, _value_in_force(old, stop_str)))
        else:
            path = projected(name) if projected is not None else None
            if path is None:
                resumed.append(_entry(name, next_str, _value_in_force(old, stop_str)))
            else:
                copied = [
                    _entry(name, entry.instant_str, entry.value)
                    for entry in path
                    if entry.instant_str > next_str
                ]
                resumed.extend(copied)
                resumed.append(_entry(name, next_str, _value_in_force(path, next_str)))
    else:
        # A change held flat to the end of the horizon: what follows it is
        # the value in force at its stop, as Parameter.update leaves it.
        resumed.append(_entry(name, next_str, _value_in_force(old, stop_str)))
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


def tree_defines(parameters: ParameterNode) -> Callable[[str], bool]:
    """``defines(path)``: whether a parameter tree has a leaf at ``path``."""

    def defines(path: str) -> bool:
        try:
            return isinstance(parameters.get_child(path), Parameter)
        except Exception:
            return False

    return defines
