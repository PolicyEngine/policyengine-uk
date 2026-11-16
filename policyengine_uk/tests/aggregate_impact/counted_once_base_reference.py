"""The counted-once check as it stood at 89bd11fec, without commentary.

Keep this independent of the production tool: it is the differential oracle
for #2773, whose fix must publish exactly what this did for every model whose
heads and totals are finite at baseline. It holds the check (``guard.py``),
how ``measure`` records and publishes its result (``record_guard_checks``,
``publishable_guard``) and how ``render`` describes it (``_guard``).
"""

from __future__ import annotations

import math
from typing import Iterable, Mapping, Optional

import numpy as np

from policyengine_uk.utils.aggregate_impact.partition import Partition
from policyengine_uk.utils.aggregate_impact.privacy import MIN_CELL, count_text, small
from policyengine_uk.utils.aggregate_impact.spec import fiscal_year_label


def _raw(sim, variable, period):
    try:
        result = sim.calculate(variable, period, unweighted=True)
    except TypeError:
        result = sim.calculate(variable, period)
    return np.asarray(getattr(result, "values", result))


def discard_formula_results(sim) -> bool:
    reset = getattr(sim, "_invalidate_all_caches", None)
    if reset is None:
        return False
    reset()
    return True


class _InputSnapshot(dict):
    def __init__(self, values, *, owner, origins):
        super().__init__(values)
        self.owner = owner
        self.origins = origins


def _visible_branches(sim):
    branches = []
    branch = sim
    while branch is not None:
        if branch.branch_name not in branches:
            branches.append(branch.branch_name)
        branch = getattr(branch, "parent_branch", None)
    if "default" not in branches:
        branches.append("default")
    return branches


def _capture_input_origins(sim, variables):
    from policyengine_uk.utils.supplied_inputs import SUPPLIED_INPUT_VARIABLES

    names = set(variables) & SUPPLIED_INPUT_VARIABLES
    if not names:
        return {}
    branches = set(_visible_branches(sim))
    keys = set(getattr(sim, "_user_input_keys", None) or ())
    model = getattr(sim, "_model_values", None) or {}
    origins = {}
    for name in names:
        if name not in sim.tax_benefit_system.variables:
            continue
        holder = sim.get_holder(name)
        slots = []
        for key in keys | set(model):
            variable, branch, period = key
            if variable != name or branch not in branches:
                continue
            value = holder._get_array_from_storage(period, branch)
            if value is None:
                continue
            marker = model.get(key)
            is_model = marker is not None and np.array_equal(marker, value)
            if key in keys or is_model:
                slots.append((branch, period, np.array(value, copy=True), is_model))
        origins[name] = tuple(slots)
    return origins


def snapshot_inputs(sim, variables) -> dict:
    variables = tuple(variables)
    discard_formula_results(sim)
    origins = _capture_input_origins(sim, variables)
    snapshot = _InputSnapshot({}, owner=sim, origins=origins)
    for variable in variables:
        if variable not in sim.tax_benefit_system.variables:
            continue
        holder = sim.get_holder(variable)
        periods = holder.get_known_periods()
        if periods:
            snapshot[variable] = [
                (period, np.array(holder.get_array(period), copy=True))
                for period in periods
            ]
    return snapshot


def _guard_snapshot(sim, snapshot, variables):
    if snapshot is None:
        return snapshot_inputs(sim, variables)
    if isinstance(snapshot, _InputSnapshot):
        if snapshot.owner is not sim:
            raise ValueError("Input snapshot belongs to a different simulation")
        return snapshot
    from policyengine_uk.utils.supplied_inputs import SUPPLIED_INPUT_VARIABLES

    origins = _capture_input_origins(sim, variables)
    for name in set(snapshot) & SUPPLIED_INPUT_VARIABLES:
        for period, value in snapshot[name]:
            if not any(
                (
                    saved_period == period and np.array_equal(saved_value, value)
                    for _, saved_period, saved_value, _ in origins.get(name, ())
                )
            ):
                raise ValueError("Plain input snapshot has no matching original slot")
    return _InputSnapshot(snapshot, owner=sim, origins=origins)


def _set_guard_value(sim, variable, period, value, touched=None):
    from policyengine_uk.utils.supplied_inputs import (
        SUPPLIED_INPUT_VARIABLES,
        set_model_value,
    )

    if touched is not None:
        touched.add(variable)
    if variable in SUPPLIED_INPUT_VARIABLES:
        set_model_value(sim, variable, period, value)
    else:
        sim.set_input(variable, period, value)


def _restore(sim, variable, snapshot):
    from policyengine_uk.utils.supplied_inputs import (
        SUPPLIED_INPUT_VARIABLES,
        drop_missing_model_values,
        drop_missing_supplied_inputs,
        set_model_value,
    )

    if variable not in SUPPLIED_INPUT_VARIABLES:
        sim.delete_arrays(variable)
        for period, values in snapshot.get(variable, []):
            sim.set_input(variable, period, values)
        return
    if not isinstance(snapshot, _InputSnapshot) or snapshot.owner is not sim:
        raise ValueError("Registered restoration needs its original input snapshot")
    if variable not in snapshot.origins:
        raise ValueError("Registered variable is absent from original origin capture")
    holder = sim.get_holder(variable)
    holder.delete_arrays(branch_name=sim.branch_name)
    drop_missing_supplied_inputs(sim, variable)
    drop_missing_model_values(sim, variable)
    for branch, period, value, is_model in snapshot.origins[variable]:
        if branch == sim.branch_name:
            if is_model:
                set_model_value(sim, variable, period, value)
            else:
                sim.set_input(variable, period, value)


def _months(year):
    from policyengine_core.periods import period as make_period

    return make_period(str(year)).get_subperiods("month")


def _household(sim, values, entity):
    values = np.asarray(values, dtype=np.float64)
    if entity == "household":
        return values
    return np.asarray(sim.map_result(values, entity, "household"), dtype=np.float64)


def _head_arrays(sim, year, variables) -> dict:
    definitions = sim.tax_benefit_system.variables
    return {
        v: _household(sim, _raw(sim, v, year), definitions[v].entity.key)
        for v in variables
    }


ABSOLUTE_SLACK_GBP = 0.02
RELATIVE_SLACK = 2e-06


def _slack(scale: np.ndarray) -> np.ndarray:
    return ABSOLUTE_SLACK_GBP + RELATIVE_SLACK * np.abs(scale)


def _response_slack(response: np.ndarray, expected: np.ndarray) -> np.ndarray:
    return ABSOLUTE_SLACK_GBP * np.abs(expected) + RELATIVE_SLACK * np.abs(response)


def _moves(
    response: np.ndarray, expected: np.ndarray, allowances: int = 1
) -> np.ndarray:
    beyond = np.abs(response) > allowances * _response_slack(response, expected)
    return beyond | ~np.isfinite(response)


def _contains(
    response: np.ndarray, expected: np.ndarray, allowances: int = 1
) -> np.ndarray:
    close = np.abs(response - expected) <= allowances * _response_slack(
        response, expected
    )
    return close | ~np.isfinite(response)


def _rises(response: np.ndarray, slack: np.ndarray) -> np.ndarray:
    return (response > slack) | ~np.isfinite(response)


def _not_finite_units(values) -> np.ndarray:
    if isinstance(values, list):
        return np.logical_or.reduce([~np.isfinite(v) for _, v in values])
    return ~np.isfinite(values)


def _held_values(at_first, baseline, units):
    if isinstance(at_first, list):
        return [
            (month, np.where(units, start, value))
            for (month, value), (_, start) in zip(at_first, baseline)
        ]
    return np.where(units, baseline, at_first)


def _households_text(households) -> str:
    if households is None:
        return f"fewer than {MIN_CELL} households"
    return count_text(households, "households")


def problem_text(kind, head, component, households, not_finite=False, weighted=True):
    clause = ", or is not finite," if not_finite and weighted else ""
    if kind == "own_head":
        text = f"{head} does not move by exactly what was added to {component}{clause}"
    elif kind == "contains":
        text = f"{head} rises one for one with {component}" + (
            clause or ", so it contains it,"
        )
    elif kind == "unconfirmed":
        text = f"{head} responds to {component}{clause}"
    elif kind == "rises":
        text = f"{head} rises{clause} when {component} does"
    elif kind == "moves":
        text = f"{head} moves{clause} when {component} does"
    elif kind == "mediated":
        text = f"{head} responds only through other heads{clause}"
    else:
        text = f"the model's {head} moves by other than its heads{clause} when {component} does"
    text += f" in {_households_text(households)}"
    if not_finite and (not weighted):
        text += ", and is not finite in households with no weight"
    return text


def _unheld_where(households, of_them=False) -> str:
    if households == 0:
        return "households with no weight"
    what = "of them" if of_them else "households"
    if households is None or small(households):
        return f"fewer than {MIN_CELL} {what}"
    return f"{households:,} {what}"


def _unheld_words(heads, component, name=str) -> str:
    names = [name(v) for v in heads]
    if len(names) == 1:
        listed, which = (names[0], "which is")
    else:
        listed = f"{', '.join(names[:-1])} and {names[-1]}"
        which = "one or more of which is"
    return f"the check could not hold {listed}, {which} not finite there once {name(component)} rises"


def not_held_note(component, head, heads, households, name=str) -> str:
    return f"in {_unheld_where(households)} {_unheld_words(heads, component, name)}, so it measured {name(head)} again there only with the other heads at their baseline values"


def _problem(
    total,
    head,
    kind,
    component,
    where,
    weights,
    perturbed,
    nan,
    not_held=(),
    unjudged=None,
):
    weighted = weights > 0
    count = int(np.count_nonzero(where & weighted))
    base = float(np.sum(weights * perturbed))
    share = float(np.sum(weights * where)) / base if base else 0.0
    not_finite = bool((where & nan).any())
    not_finite_weighted = bool((where & nan & weighted).any())
    unjudged = np.zeros_like(where) if unjudged is None else unjudged & where
    unheld = int(np.count_nonzero(unjudged & weighted)) if not_held else 0
    text = problem_text(kind, head, component, count, not_finite, not_finite_weighted)
    message = f"{total}: {text}"
    if kind == "unconfirmed":
        message += f" where {_unheld_words(list(not_held), component)}, so it could not confirm whether {head} contains {component}"
    elif not_held:
        message += f" (in {_unheld_where(unheld, of_them=True)} {_unheld_words(list(not_held), component)}, so it could not show that {head} responds only through other heads)"
    return {
        "total": total,
        "head": head,
        "kind": kind,
        "households": count,
        "share": share,
        "message": message,
        "not_finite": not_finite,
        "not_finite_weighted": not_finite_weighted,
        "heads_not_held": list(not_held),
        "households_not_held": unheld,
        "where": where,
        "nan": nan,
        "unjudged": unjudged,
    }


def judge_total(
    *,
    total: str,
    is_tax: bool,
    component: str,
    own_variable: str,
    declared_double_count: bool,
    zero_baseline: bool,
    weights: np.ndarray,
    expected: np.ndarray,
    head_changes: Mapping[str, np.ndarray],
    head_scales: Mapping[str, np.ndarray],
    model_change: Optional[np.ndarray],
    model_scale: Optional[np.ndarray],
    allowed_readers: Iterable[str],
    second_changes: Optional[Mapping[str, np.ndarray]] = None,
) -> dict:
    added = float(np.sum(weights * expected))
    allowed = set(allowed_readers)
    perturbed = expected > 0
    responses, problems, screens, own_problem = ({}, [], [], None)

    def problem(head, kind, where, nan):
        return _problem(total, head, kind, component, where, weights, perturbed, nan)

    for variable, change in head_changes.items():
        responses[variable] = float(np.sum(weights * change)) / added if added else 0.0
        slack = _slack(head_scales[variable])
        if variable == own_variable:
            off = (np.abs(change - expected) > slack) | ~np.isfinite(change)
            if off.any():
                own_problem = problem(variable, "own_head", off, ~np.isfinite(change))
            continue
        reader = variable in allowed or (zero_baseline and (not is_tax))
        if reader:
            if second_changes is not None:
                slope = second_changes[variable] - change
                response_slack = _response_slack(slope, expected)
                containing = perturbed & _contains(slope, expected, 2)
                linear = perturbed & (np.abs(slope) > 2 * response_slack) & ~containing
                if linear.any():
                    screens.append(
                        problem(variable, "contains", linear, ~np.isfinite(slope))
                    )
            else:
                slope = change
                containing = perturbed & _contains(change, expected)
            containing = containing | ~np.isfinite(slope)
            if containing.any():
                problems.append(
                    problem(variable, "contains", containing, ~np.isfinite(slope))
                )
        elif is_tax:
            moved = _moves(change, expected)
            if moved.any():
                problems.append(problem(variable, "moves", moved, ~np.isfinite(change)))
        else:
            rises = _rises(change, slack)
            if rises.any():
                problems.append(problem(variable, "rises", rises, ~np.isfinite(change)))
    partition_coefficient = float(sum(responses.values()))
    model_coefficient = None
    if model_change is not None:
        model_coefficient = (
            float(np.sum(weights * model_change)) / added if added else 0.0
        )
        heads_change = sum(head_changes.values())
        if declared_double_count:
            heads_change = heads_change + expected
        not_finite = ~np.isfinite(model_change) | ~np.isfinite(heads_change)
        beyond = np.abs(model_change - heads_change) > _slack(model_scale)
        mismatch = beyond | not_finite
        if mismatch.any():
            problems.append(problem(total, "model_total", mismatch, not_finite))
    return {
        "responses": responses,
        "coefficient": partition_coefficient,
        "model_coefficient": model_coefficient,
        "own_problem": own_problem,
        "problems": problems,
        "screens": screens,
    }


def _perturb(
    sim, variable, year, baseline, added, monthly, hold=(), held_at=None, touched=None
):
    discard_formula_results(sim)
    if monthly:
        for month, values in baseline[variable]:
            _set_guard_value(sim, variable, month, values + added / 12, touched=touched)
    else:
        _set_guard_value(
            sim, variable, year, baseline[variable] + added, touched=touched
        )
    held_at = baseline if held_at is None else held_at
    for held in hold:
        if isinstance(held_at[held], list):
            for month, values in held_at[held]:
                _set_guard_value(sim, held, month, values, touched=touched)
        else:
            _set_guard_value(sim, held, year, held_at[held], touched=touched)


def _capture(sim, variables, year, layout) -> dict:
    out = {}
    for v in variables:
        if isinstance(layout[v], list):
            out[v] = [
                (month, _raw(sim, v, month).astype(np.float64))
                for month, _ in layout[v]
            ]
        else:
            out[v] = _raw(sim, v, year).astype(np.float64)
    return out


def breaks_on_slope(kind, where, expected, slack, slope):
    if kind == "contains":
        return where & _contains(slope, expected, allowances=2)
    if kind == "rises":
        return where & _rises(slope, 2 * slack)
    if kind == "moves":
        return where & _moves(slope, expected, allowances=2)
    return where


def still_breaks(kind, where, expected, slack, first, second=None):
    if kind == "contains":
        if second is not None:
            return where & _contains(second - first, expected, allowances=2)
        return where & _contains(first, expected)
    if kind == "rises":
        return where & _rises(first, slack)
    if kind == "moves":
        return where & _moves(first, expected)
    return where


def _held_breaks(kind, where, expected, slack, first, second, slope_held, unjudged):
    held_at_baseline = still_breaks(kind, where, expected, slack, first, second)
    judged = where & ~unjudged
    return held_at_baseline | breaks_on_slope(kind, judged, expected, slack, slope_held)


def _held_nan(kind, first, second, slope_held, unjudged):
    nan = ~np.isfinite(first) | ~np.isfinite(slope_held) & ~unjudged
    if kind == "contains" and second is not None:
        nan = nan | ~np.isfinite(second)
    return nan


DIRECT_KINDS = ("contains", "rises", "moves")


def counted_once(
    sim,
    partition: Partition,
    year: int,
    tolerance: float,
    snapshot: Optional[Mapping] = None,
    active: Iterable[str] = (),
    variables_to_check: Optional[Iterable[str]] = None,
) -> dict:
    if not discard_formula_results(sim):
        return {
            "status": "skipped",
            "reason": "this policyengine-core has no way to discard formula results",
        }
    snapshot = _guard_snapshot(sim, snapshot, partition.component_variables())
    active = set(active)
    definitions = sim.tax_benefit_system.variables
    totals = [t for t in partition.totals if partition.heads_in(t, active)]
    heads_of = {t: [h.variable for h in partition.heads_in(t, active)] for t in totals}
    all_heads = list(dict.fromkeys((v for t in totals for v in heads_of[t])))
    model_totals = [t for t in totals if t in definitions]
    hw = _raw(sim, "household_weight", year).astype(np.float64)
    heads0 = _head_arrays(sim, year, all_heads)
    model0 = {t: _raw(sim, t, year).astype(np.float64) for t in model_totals}
    baseline = {}
    for variable in partition.component_variables():
        if definitions[variable].definition_period == "month":
            baseline[variable] = [
                (month, _raw(sim, variable, month).astype(np.float64))
                for month in _months(year)
            ]
        else:
            baseline[variable] = _raw(sim, variable, year).astype(np.float64)
    declared = {dc.variable: dc for dc in partition.double_counts}
    head_by_variable = {h.variable: h for h in partition.heads}
    selected = None if variables_to_check is None else set(variables_to_check)
    results, double_count_results = ([], [])
    touched = set()
    try:
        for variable in partition.component_variables():
            if selected is not None and variable not in selected:
                continue
            definition = definitions[variable]
            entity = definition.entity.key
            in_totals = [
                t for t in totals if variable in partition.components(t, active)
            ]
            record = {
                "variable": variable,
                "totals": in_totals,
                "coefficients": {},
                "model_coefficients": {},
                "responses": {},
                "problems": [],
                "mediated": [],
                "heads_held_skipped": False,
                "heads_not_held": {},
                "households_not_held": {},
                "units": 0,
                "status": "pass",
                "detail": "",
            }
            if definition.value_type is not float:
                record.update(status="skipped", detail="not a money variable")
                results.append(record)
                continue
            monthly = definition.definition_period == "month"
            year_values = (
                sum((values for _, values in baseline[variable]))
                if monthly
                else baseline[variable]
            )
            nonzero = year_values != 0
            zero_baseline = not bool(nonzero.any())
            mask = np.ones_like(nonzero) if zero_baseline else nonzero
            added = mask.astype(np.float64)
            expected = _household(sim, added, entity)
            record["units"] = int(round(float(np.sum(expected[hw > 0]))))
            if not float(np.sum(hw * expected)) > 0:
                record.update(
                    status="skipped",
                    detail="non-zero only in households with no weight",
                )
                results.append(record)
                continue
            own = declared[variable].contained_in if variable in declared else variable
            own_head = head_by_variable[own]
            needed = list(dict.fromkeys((v for t in in_totals for v in heads_of[t])))
            readers_of = {
                total: [
                    v
                    for v in heads_of[total]
                    if own_head.id in head_by_variable[v].reads
                ]
                for total in in_totals
            }
            _perturb(sim, variable, year, baseline, added, monthly, touched=touched)
            heads1 = _head_arrays(sim, year, needed)
            model1 = {
                t: _raw(sim, t, year).astype(np.float64)
                for t in in_totals
                if t in model0
            }
            may_respond = {
                v
                for total in in_totals
                for v in heads_of[total]
                if v != own
                and (
                    v in readers_of[total]
                    or (zero_baseline and (not partition.is_tax_total(total)))
                )
            }
            heads2 = None
            if may_respond:
                _perturb(
                    sim, variable, year, baseline, 2 * added, monthly, touched=touched
                )
                heads2 = _head_arrays(sim, year, sorted(may_respond))
            problems, screens = ([], [])
            for total in in_totals:
                verdict = judge_total(
                    total=total,
                    is_tax=partition.is_tax_total(total),
                    component=variable,
                    own_variable=own,
                    declared_double_count=variable in declared
                    and total in declared[variable].totals,
                    zero_baseline=zero_baseline,
                    weights=hw,
                    expected=expected,
                    head_changes={v: heads1[v] - heads0[v] for v in heads_of[total]},
                    head_scales={v: heads0[v] for v in heads_of[total]},
                    model_change=model1[total] - model0[total]
                    if total in model1
                    else None,
                    model_scale=model0.get(total),
                    allowed_readers=readers_of[total],
                    second_changes=None
                    if heads2 is None
                    else {v: heads2[v] - heads0[v] for v in heads2},
                )
                record["coefficients"][total] = verdict["coefficient"]
                if verdict["model_coefficient"] is not None:
                    record["model_coefficients"][total] = verdict["model_coefficient"]
                record["responses"][total] = {
                    v: r
                    for v, r in verdict["responses"].items()
                    if not abs(r) <= tolerance
                }
                problems += verdict["problems"]
                screens += verdict["screens"]
                if verdict["own_problem"] and variable not in declared:
                    problems.append(verdict["own_problem"])
            mediated = []
            perturbed_units = expected > 0
            for head in dict.fromkeys(
                [p["head"] for p in problems if p["kind"] in DIRECT_KINDS]
                + [screen["head"] for screen in screens]
            ):
                held = [v for v in all_heads if v not in (variable, own, head)]
                _perturb(
                    sim,
                    variable,
                    year,
                    baseline,
                    added,
                    monthly,
                    hold=held,
                    touched=touched,
                )
                first = _head_arrays(sim, year, [head])[head] - heads0[head]
                second = None
                if any(
                    (
                        p["head"] == head and p["kind"] == "contains"
                        for p in problems + screens
                    )
                ):
                    _perturb(
                        sim,
                        variable,
                        year,
                        baseline,
                        2 * added,
                        monthly,
                        hold=held,
                        touched=touched,
                    )
                    second = _head_arrays(sim, year, [head])[head] - heads0[head]
                for v in held:
                    _restore(sim, v, snapshot)
                _perturb(sim, variable, year, baseline, added, monthly, touched=touched)
                at_first = _capture(sim, held, year, baseline)
                head_first = _head_arrays(sim, year, [head])[head]
                held_at, unheld_in = ({}, {})
                for v in held:
                    units = _not_finite_units(at_first[v])
                    held_at[v] = at_first[v]
                    if units.any():
                        held_at[v] = _held_values(at_first[v], baseline[v], units)
                        entity_key = definitions[v].entity.key
                        unheld_in[v] = _household(sim, units, entity_key) > 0
                _perturb(
                    sim,
                    variable,
                    year,
                    baseline,
                    2 * added,
                    monthly,
                    hold=held,
                    held_at=held_at,
                    touched=touched,
                )
                slope_held = _head_arrays(sim, year, [head])[head] - head_first
                for v in held:
                    _restore(sim, v, snapshot)
                not_held = list(unheld_in)
                unjudged = np.zeros(len(hw), dtype=bool)
                for v in not_held:
                    unjudged = unjudged | unheld_in[v]
                if not_held:
                    record["heads_not_held"][head] = not_held
                    record["households_not_held"][head] = int(
                        np.count_nonzero(unjudged & (hw > 0))
                    )

                def unheld(where):
                    return [v for v in not_held if bool((unheld_in[v] & where).any())]

                slack = _slack(heads0[head])
                kept = []
                for p in problems:
                    if p["head"] != head or p["kind"] not in DIRECT_KINDS:
                        kept.append(p)
                        continue
                    breaks = _held_breaks(
                        p["kind"],
                        p["where"],
                        expected,
                        slack,
                        first,
                        second,
                        slope_held,
                        unjudged,
                    )
                    rests = p["where"] & unjudged & ~breaks
                    direct = breaks | rests
                    cleared = p["where"] & ~direct
                    if cleared.any():
                        via = [
                            v
                            for v in needed
                            if v not in (variable, own, head)
                            and bool(
                                (
                                    np.abs(heads1[v] - heads0[v])[cleared]
                                    > _slack(heads0[v])[cleared]
                                ).any()
                            )
                        ]
                        nan = cleared & p["nan"]
                        mediated.append(
                            {
                                "total": p["total"],
                                "head": head,
                                "kind": p["kind"],
                                "households": int(np.count_nonzero(cleared & (hw > 0))),
                                "via": via,
                                "not_finite": bool(nan.any()),
                                "not_finite_weighted": bool((nan & (hw > 0)).any()),
                            }
                        )
                    if direct.any():
                        kept.append(
                            _problem(
                                p["total"],
                                head,
                                p["kind"],
                                variable,
                                direct,
                                hw,
                                perturbed_units,
                                p["nan"]
                                | _held_nan(
                                    p["kind"], first, second, slope_held, unjudged
                                ),
                                unheld(rests),
                                rests,
                            )
                        )
                for screen in screens:
                    if screen["head"] != head:
                        continue
                    confirmed = _held_breaks(
                        "contains",
                        screen["where"],
                        expected,
                        slack,
                        first,
                        second,
                        slope_held,
                        unjudged,
                    )
                    unconfirmed = screen["where"] & unjudged & ~confirmed
                    nan = _held_nan("contains", first, second, slope_held, unjudged)
                    if confirmed.any():
                        not_held_there, rests = ((), None)
                        same = next(
                            (
                                k
                                for k in kept
                                if (k["total"], k["head"], k["kind"])
                                == (screen["total"], head, "contains")
                            ),
                            None,
                        )
                        if same is not None:
                            kept.remove(same)
                            confirmed = confirmed | same["where"]
                            not_held_there, rests = (
                                same["heads_not_held"],
                                same["unjudged"],
                            )
                        kept.append(
                            _problem(
                                screen["total"],
                                head,
                                "contains",
                                variable,
                                confirmed,
                                hw,
                                perturbed_units,
                                nan if same is None else nan | same["nan"],
                                not_held_there,
                                rests,
                            )
                        )
                    if unconfirmed.any():
                        kept.append(
                            _problem(
                                screen["total"],
                                head,
                                "unconfirmed",
                                variable,
                                unconfirmed,
                                hw,
                                perturbed_units,
                                nan,
                                unheld(unconfirmed),
                                unconfirmed,
                            )
                        )
                problems = kept
            problems = [
                {k: v for k, v in p.items() if k not in ("where", "nan", "unjudged")}
                for p in problems
            ]
            record["mediated"] = mediated
            record["heads_held_skipped"] = bool(record["heads_not_held"])
            if variable in declared:
                dc = declared[variable]
                container_change = heads1[own] - heads0[own]
                k = float(np.sum(hw * container_change)) / float(np.sum(hw * expected))
                finite = bool(np.isfinite(container_change).all())
                present = finite and (
                    not bool(
                        (
                            np.abs(container_change - expected) > _slack(heads0[own])
                        ).any()
                    )
                )
                row = {
                    "variable": variable,
                    "contained_in": dc.contained_in,
                    "coefficient": k,
                    "issue": dc.issue,
                    "status": "pass" if present else "fail",
                    "not_finite": not finite,
                    "detail": ""
                    if present
                    else f"{dc.contained_in} moves by {k:.4f} per unit of {variable}: the model no longer counts it twice, so remove the declaration and give it its own head",
                }
                if not finite:
                    row["detail"] = (
                        f"{dc.contained_in} is not finite when {variable} rises, so the check cannot show that {dc.contained_in} still contains {variable}"
                    )
                double_count_results.append(row)
            if problems:
                record.update(
                    status="fail",
                    problems=problems,
                    detail="; ".join((p["message"] for p in problems)),
                )
            else:
                record["detail"] = "; ".join(
                    (
                        not_held_note(
                            variable, head, heads, record["households_not_held"][head]
                        )
                        for head, heads in record["heads_not_held"].items()
                    )
                )
            results.append(record)
            _restore(sim, variable, snapshot)
    finally:
        for variable in sorted(touched):
            _restore(sim, variable, snapshot)
    discard_formula_results(sim)
    heads_again = _head_arrays(sim, year, all_heads)
    reproduces = all((np.array_equal(heads_again[v], heads0[v]) for v in all_heads))
    return {
        "status": "ran",
        "year": year,
        "tolerance": tolerance,
        "components": results,
        "double_counts": double_count_results,
        "reset_reproduces_baseline": bool(reproduces),
    }


def publishable_guard(guard: dict) -> dict:
    out = dict(guard)
    components = []
    for row in guard.get("components") or []:
        row = dict(row)
        few_units = small(row.get("units") or 0)
        if few_units:
            row["units"] = None
            for key in ("responses", "coefficients", "model_coefficients"):
                if key in row:
                    row[key] = {}
        for key in ("problems", "mediated"):
            cleaned = []
            for item in row.get(key) or []:
                item = dict(item)
                if few_units or small(item.get("households") or 0):
                    item.pop("share", None)
                if small(item.get("households") or 0):
                    item["households"] = None
                if small(item.get("households_not_held") or 0):
                    item["households_not_held"] = None
                cleaned.append(item)
            row[key] = cleaned
        if "households_not_held" in row:
            row["households_not_held"] = {
                head: None if small(count or 0) else count
                for head, count in row["households_not_held"].items()
            }
        components.append(row)
    if "components" in guard:
        out["components"] = components
    units = {
        row.get("variable"): row.get("units") for row in guard.get("components") or []
    }
    double_counts = []
    for row in guard.get("double_counts") or []:
        row = dict(row)
        if small(units.get(row.get("variable")) or 0):
            row["coefficient"] = None
            if row.get("status") != "pass" and (not row.get("not_finite")):
                row["detail"] = (
                    f"{row['contained_in']} no longer moves one for one with {row['variable']} (fewer than {MIN_CELL} units): the model no longer counts it twice, so remove the declaration and give it its own head"
                )
        double_counts.append(row)
    if "double_counts" in guard:
        out["double_counts"] = double_counts
    return out


def record_guard_checks(rec, guard: dict) -> None:
    for result in guard.get("components", []):
        check_id = f"counted_once:{result['variable']}"
        label = f"Raising {result['variable']} by £1 raises its own head by £1, moves no other tax head and raises no other benefit"
        if result["status"] == "skipped":
            rec.check(
                check_id,
                label,
                None,
                result["detail"],
                section="counted_once",
                scope="",
            )
        elif result["status"] == "pass":
            rec.check(
                check_id,
                label,
                True,
                section="counted_once",
                scope="",
                note=result["detail"],
            )
        for item in result.get("problems") or []:
            rec.check(
                check_id,
                label,
                False,
                item["message"],
                section="counted_once",
                scope=f"{item['total']}:{item['head']}:{item['kind']}",
            )
    for result in publishable_guard(guard).get("double_counts", []):
        rec.check(
            f"double_count_present:{result['variable']}",
            f"{result['variable']} is still contained in {result['contained_in']}",
            result["status"] == "pass",
            result["detail"],
            section="counted_once",
        )
    if "reset_reproduces_baseline" in guard:
        rec.check(
            "counted_once:reset_reproduces_baseline",
            "The counted-once check leaves the baseline unchanged",
            bool(guard["reset_reproduces_baseline"]),
            "recomputed baseline totals differ from the first run",
            section="counted_once",
        )
    rec.check(
        "counted_once:ran",
        "The counted-once check ran",
        guard.get("status") == "ran",
        guard.get("reason", ""),
        severity="warn",
        section="counted_once",
    )


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _guard(summary) -> str:
    guard = (summary.get("head") or {}).get("guard") or {}
    if guard.get("status") != "ran":
        return f"Counted-once check not run: {guard.get('reason', 'unknown reason')}."
    components = guard.get("components", [])
    tested = [c for c in components if c["status"] != "skipped"]
    failed = [c for c in tested if c["status"] == "fail"]
    skipped = [c for c in components if c["status"] == "skipped"]
    lines = [
        f"The check raised each of {len(tested)} components by £1 per unit in {fiscal_year_label(guard['year'])} and read every head of its totals household by household: its own head must rise by exactly £1, no other tax head may move, no other benefit may rise, and the model's own total must move by what its heads moved. A response that is not finite breaks every rule. The check measures a head that breaks a rule twice more: once holding every other head at its baseline value, and once holding every other head at its value after the first £1 while the component rises again. The head fails where either measurement still shows the response. The check cannot hold a head at a value that is not finite. In each unit where another head is not finite after the first £1, it holds that head at its baseline value, and the second measurement judges no household the unit belongs to. There a head fails wherever it first broke a rule, or wherever the check could not confirm whether its response contains the component. {len(failed)} failed and the check skipped {len(skipped)}."
    ]
    for c in failed:
        problems = c.get("problems") or [{"message": c.get("detail", "")}]
        lines.append(
            f"- `{c['variable']}`: " + "; ".join((p["message"] for p in problems))
        )
    for c in skipped:
        lines.append(f"- `{c['variable']}` skipped: {c.get('detail', '')}")
    code = "`{}`".format
    for c in tested:
        counts = c.get("households_not_held") or {}
        for head, heads in (c.get("heads_not_held") or {}).items():
            note = not_held_note(c["variable"], head, heads, counts.get(head), code)
            lines.append(f"- `{c['variable']}`: {note}")
    for c in tested:
        for m in c.get("mediated") or []:
            moved = ", ".join((code(v) for v in m["via"])) or "none"
            text = problem_text(
                "mediated",
                code(m["head"]),
                code(c["variable"]),
                m.get("households"),
                m.get("not_finite", False),
                m.get("not_finite_weighted", True),
            )
            lines.append(
                f"- `{c['variable']}`: {text} (other heads that moved there: {moved}; {m['total']}; not a failure)"
            )
    for dc in guard.get("double_counts", []):
        if dc.get("not_finite"):
            lines.append(
                f"- declared double count `{dc['variable']}`: `{dc['contained_in']}` is NOT FINITE when `{dc['variable']}` rises, so the check cannot show that `{dc['contained_in']}` still contains `{dc['variable']}` ({dc['issue']})"
            )
            continue
        state = "still contained" if dc["status"] == "pass" else "NO LONGER contained"
        coefficient = (
            f"coefficient {dc['coefficient']:.3f}"
            if _finite(dc.get("coefficient"))
            else "coefficient not shown, fewer than 10 units"
        )
        lines.append(
            f"- declared double count `{dc['variable']}` is {state} in `{dc['contained_in']}` ({coefficient}; {dc['issue']})"
        )
    return "\n".join(lines)
