"""The counted-once check: every component enters each total exactly once.

For each component of a partition total, the check adds 1 to every unit
where the component is non-zero, recomputes every head of the totals it
belongs to, and reads each head's response household by household. For a
total T and a component c:

- c's own head (c itself, or the head a declared double count is contained
  in) must rise by exactly 1 per unit added;
- on a tax total, no other head may move at all: a head that moves contains
  c, or reads it;
- on a spending total, no other head may rise in any household. Means tests
  may lower other benefits when one rises (Pension Credit falls as State
  Pension rises), but a benefit that rises with another either contains it
  or pays more to people with more income. Rises and falls are not netted,
  so a fall elsewhere cannot hide a double count;
- the model's own total must move by exactly what its heads moved, plus one
  more per unit if c is a declared double count of T. This catches a total
  whose formula adds a component twice even when that component is zero.

A head that declares a read of c's head (``reads`` in the partition) may
respond, unless it responds one for one, which is containment. A spending
component that is zero for every unit is perturbed everywhere, which makes
recipients of non-recipients; other heads may then rise through passporting,
so only a one-for-one response fails.

The check reuses one simulation. It takes its snapshot of supplied inputs
only after discarding formula results, so a value some formula computed
earlier is never frozen as an input. Between perturbations it discards every
formula result, and restores any input it overrode; at the end it recomputes
the baseline and requires it to match the first computation exactly.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Optional

import numpy as np

from .partition import Partition


def _raw(sim, variable, period):
    try:
        result = sim.calculate(variable, period, unweighted=True)
    except TypeError:
        result = sim.calculate(variable, period)
    return np.asarray(getattr(result, "values", result))


def discard_formula_results(sim) -> bool:
    """Drop every calculated value, keeping supplied inputs. False if unsupported."""
    reset = getattr(sim, "_invalidate_all_caches", None)
    if reset is None:
        return False
    reset()
    return True


def snapshot_inputs(sim, variables) -> dict:
    """Copy the supplied input arrays of ``variables``.

    Formula results are discarded first: a holder's known periods include
    calculated values, and restoring one of those as an input would freeze
    it for every later perturbation.
    """
    discard_formula_results(sim)
    snapshot = {}
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


def _restore(sim, variable, snapshot):
    sim.delete_arrays(variable)
    for period, values in snapshot.get(variable, []):
        sim.set_input(variable, period, values)


def _months(year):
    from policyengine_core.periods import period as make_period

    return make_period(str(year)).get_subperiods("month")


def _household(sim, values, entity):
    values = np.asarray(values, dtype=np.float64)
    if entity == "household":
        return values
    return np.asarray(sim.map_result(values, entity, "household"), dtype=np.float64)


def _head_arrays(sim, year, variables) -> dict:
    """Each variable's values summed to households."""
    definitions = sim.tax_benefit_system.variables
    return {
        v: _household(sim, _raw(sim, v, year), definitions[v].entity.key)
        for v in variables
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
    model_change: Optional[np.ndarray],
    allowed_readers: Iterable[str],
    tolerance: float,
) -> dict:
    """Apply the counted-once rules to one total's responses.

    ``head_changes`` maps each head variable of the total to its change by
    household; ``expected`` is what was added to the component by household.
    Returns the responses per unit added, the problem with the component's
    own head (if it did not rise one for one) and the other problems.
    """
    added = float(np.sum(weights * expected))
    allowed = set(allowed_readers)
    responses, problems, own_problem = {}, [], None
    for variable, change in head_changes.items():
        net = float(np.sum(weights * change)) / added
        rise = float(np.sum(weights * np.maximum(change, 0.0))) / added
        moved = float(np.sum(weights * np.abs(change))) / added
        responses[variable] = net
        if variable == own_variable:
            off = float(np.sum(weights * np.abs(change - expected))) / added
            if off > tolerance:
                own_problem = f"{total}: {variable} moves by {net:.4f} per unit of {component}, not 1"
            continue
        one_for_one = abs(net - 1) <= tolerance and abs(rise - 1) <= tolerance
        if variable in allowed or (zero_baseline and not is_tax):
            if one_for_one:
                problems.append(
                    f"{total}: {variable} rises one for one with {component}, so it contains it"
                )
        elif is_tax:
            if moved > tolerance:
                problems.append(
                    f"{total}: {variable} moves by {net:+.4f} per unit of {component}"
                )
        elif rise > tolerance:
            problems.append(
                f"{total}: {variable} rises by {rise:.4f} per unit of {component}"
            )
    partition_coefficient = float(sum(responses.values()))
    model_coefficient = None
    if model_change is not None:
        model_coefficient = float(np.sum(weights * model_change)) / added
        expected_model = partition_coefficient + (1.0 if declared_double_count else 0.0)
        if abs(model_coefficient - expected_model) > tolerance:
            problems.append(
                f"the model's {total} moves by {model_coefficient:.4f} per unit of "
                f"{component}, but its heads account for {expected_model:.4f}"
            )
    return {
        "responses": responses,
        "coefficient": partition_coefficient,
        "model_coefficient": model_coefficient,
        "own_problem": own_problem,
        "problems": problems,
    }


def counted_once(
    sim,
    partition: Partition,
    year: int,
    tolerance: float,
    snapshot: Optional[Mapping] = None,
    active: Iterable[str] = (),
    variables_to_check: Optional[Iterable[str]] = None,
) -> dict:
    """Perturb each component (or those in ``variables_to_check``) once."""
    if not discard_formula_results(sim):
        return {
            "status": "skipped",
            "reason": "this policyengine-core has no way to discard formula results",
        }
    snapshot = snapshot or {}
    active = set(active)
    definitions = sim.tax_benefit_system.variables
    totals = [t for t in partition.totals if partition.heads_in(t, active)]
    heads_of = {t: [h.variable for h in partition.heads_in(t, active)] for t in totals}
    all_heads = list(dict.fromkeys(v for t in totals for v in heads_of[t]))
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
    results, double_count_results = [], []
    for variable in partition.component_variables():
        if selected is not None and variable not in selected:
            continue
        definition = definitions[variable]
        entity = definition.entity.key
        in_totals = [t for t in totals if variable in partition.components(t, active)]
        record = {
            "variable": variable,
            "totals": in_totals,
            "coefficients": {},
            "model_coefficients": {},
            "responses": {},
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
            sum(values for _, values in baseline[variable])
            if monthly
            else baseline[variable]
        )
        nonzero = year_values != 0
        zero_baseline = not bool(nonzero.any())
        mask = np.ones_like(nonzero) if zero_baseline else nonzero
        added = mask.astype(np.float64)
        expected = _household(sim, added, entity)
        record["units"] = int(mask.sum())
        own = declared[variable].contained_in if variable in declared else variable
        own_head = head_by_variable[own]

        discard_formula_results(sim)
        if monthly:
            for month, values in baseline[variable]:
                sim.set_input(variable, month, values + added / 12)
        else:
            sim.set_input(variable, year, baseline[variable] + added)
        needed = list(dict.fromkeys(v for t in in_totals for v in heads_of[t]))
        heads1 = _head_arrays(sim, year, needed)
        problems = []
        for total in in_totals:
            readers = [
                v for v in heads_of[total] if own_head.id in head_by_variable[v].reads
            ]
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
                model_change=(
                    _raw(sim, total, year).astype(np.float64) - model0[total]
                    if total in model0
                    else None
                ),
                allowed_readers=readers,
                tolerance=tolerance,
            )
            record["coefficients"][total] = verdict["coefficient"]
            if verdict["model_coefficient"] is not None:
                record["model_coefficients"][total] = verdict["model_coefficient"]
            record["responses"][total] = {
                v: r for v, r in verdict["responses"].items() if abs(r) > tolerance
            }
            problems += verdict["problems"]
            # A declared double count whose container no longer moves is
            # reported once, as a stale declaration, below.
            if verdict["own_problem"] and variable not in declared:
                problems.append(verdict["own_problem"])
        if variable in declared:
            dc = declared[variable]
            container_change = heads1[own] - heads0[own]
            off = float(np.sum(hw * np.abs(container_change - expected))) / float(
                np.sum(hw * expected)
            )
            k = float(np.sum(hw * container_change)) / float(np.sum(hw * expected))
            present = off <= tolerance
            double_count_results.append(
                {
                    "variable": variable,
                    "contained_in": dc.contained_in,
                    "coefficient": k,
                    "issue": dc.issue,
                    "status": "pass" if present else "fail",
                    "detail": ""
                    if present
                    else (
                        f"{dc.contained_in} moves by {k:.4f} per unit of {variable}: "
                        "the model no longer counts it twice, so remove the "
                        "declaration and give it its own head"
                    ),
                }
            )
        if problems:
            record.update(status="fail", detail="; ".join(problems))
        results.append(record)
        _restore(sim, variable, snapshot)

    discard_formula_results(sim)
    heads_again = _head_arrays(sim, year, all_heads)
    reproduces = all(np.array_equal(heads_again[v], heads0[v]) for v in all_heads)
    return {
        "status": "ran",
        "year": year,
        "tolerance": tolerance,
        "components": results,
        "double_counts": double_count_results,
        "reset_reproduces_baseline": bool(reproduces),
    }
