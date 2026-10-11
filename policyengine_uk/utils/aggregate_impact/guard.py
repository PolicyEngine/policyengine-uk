"""The counted-once check: every component enters each total exactly once.

For each component of a partition total, the check adds 1 to every unit
where the component is non-zero, recomputes the partition's heads, and
measures how much each total it belongs to moved per unit added (its
coefficient). Heads name one variable each, so a coefficient above 1 means
another head's variable contains the component as well: a double count of
the kind #2159 reports. On tax totals nothing should offset the addition, so
the coefficient must be exactly 1. On spending totals means tests can claw
the addition back (Pension Credit falls when State Pension rises), so the
coefficient may be below 1 but never above it: above 1 means either a double
count or another benefit rising when a household's income rises. Households
whose spending jumps far beyond the addition have crossed an eligibility
threshold; they are left out of the coefficient and counted instead.

A declared double count (``model_double_counts``) is perturbed too: its
coefficient in its container must still be 1, or the declaration is stale.

The check reuses one simulation. Between perturbations it discards every
formula result and keeps the supplied inputs, then restores any input it
overrode; at the end it recomputes the baseline and requires it to match the
first computation exactly.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Optional

import numpy as np

from .partition import Partition

# On spending totals, a household's change counts as an eligibility change
# (and is left out of the coefficient) when it differs from what was added by
# more than this many pounds, or this many times what was added.
ELIGIBILITY_JUMP_GBP = 50.0
ELIGIBILITY_JUMP_FACTOR = 20.0


def _raw(sim, variable, period):
    try:
        result = sim.calculate(variable, period, unweighted=True)
    except TypeError:
        result = sim.calculate(variable, period)
    return np.asarray(getattr(result, "values", result))


def snapshot_inputs(sim, variables) -> dict:
    """Copy the supplied input arrays of ``variables`` before any calculation."""
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


def _totals_hh(sim, partition, year, totals, active=()):
    out = {}
    for total in totals:
        hh = None
        for head in partition.heads_in(total, active):
            values = _raw(sim, head.variable, year)
            entity = sim.tax_benefit_system.variables[head.variable].entity.key
            mapped = _household(sim, values, entity)
            hh = mapped if hh is None else hh + mapped
        out[total] = hh
    return out


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
    reset = getattr(sim, "_invalidate_all_caches", None)
    if reset is None:
        return {
            "status": "skipped",
            "reason": "this policyengine-core has no way to discard formula results",
        }
    snapshot = snapshot or {}
    variables = sim.tax_benefit_system.variables
    model_totals = [t for t in partition.totals if t in variables]
    partition_totals = [t for t in partition.totals if partition.heads_in(t)]

    reset()
    hw = _raw(sim, "household_weight", year).astype(np.float64)
    heads0 = _totals_hh(sim, partition, year, partition_totals, active)
    model0 = {t: _raw(sim, t, year).astype(np.float64) for t in model_totals}
    containers = {dc.contained_in for dc in partition.double_counts}
    container0 = {
        c: _household(sim, _raw(sim, c, year), variables[c].entity.key)
        for c in containers
    }
    baseline = {}
    for variable in partition.component_variables():
        definition = variables[variable]
        if definition.definition_period == "month":
            baseline[variable] = [
                (month, _raw(sim, variable, month).astype(np.float64))
                for month in _months(year)
            ]
        else:
            baseline[variable] = _raw(sim, variable, year).astype(np.float64)

    results, double_count_results = [], []
    declared = {dc.variable: dc for dc in partition.double_counts}
    selected = None if variables_to_check is None else set(variables_to_check)
    for variable in partition.component_variables():
        if selected is not None and variable not in selected:
            continue
        definition = variables[variable]
        entity = definition.entity.key
        totals = [
            t for t in partition_totals if variable in partition.components(t, active)
        ]
        tax_totals = [t for t in totals if partition.is_tax_total(t)]
        record = {
            "variable": variable,
            "totals": totals,
            "coefficients": {},
            "model_coefficients": {},
            "units": 0,
            "status": "pass",
            "detail": "",
        }
        if definition.value_type is not float:
            record.update(status="skipped", detail="not a money variable")
            results.append(record)
            continue
        if definition.definition_period == "month":
            year_values = sum(values for _, values in baseline[variable])
        else:
            year_values = baseline[variable]
        nonzero = year_values != 0
        if nonzero.any():
            mask = nonzero
        elif tax_totals:
            # A tax that is zero everywhere can still be tested: taxes don't
            # passport anyone to anything.
            mask = np.ones_like(nonzero)
        else:
            record.update(
                status="skipped",
                detail=(
                    "zero for every unit; adding to it would create recipients, "
                    "whom passporting rules could treat differently"
                ),
            )
            results.append(record)
            continue
        added = mask.astype(np.float64)
        expected = _household(sim, added, entity)
        expected_total = float(np.sum(hw * expected))
        record["units"] = int(mask.sum())

        reset()
        if definition.definition_period == "month":
            for month, values in baseline[variable]:
                sim.set_input(variable, month, values + added / 12)
        else:
            sim.set_input(variable, year, baseline[variable] + added)
        heads1 = _totals_hh(sim, partition, year, totals, active)
        problems = []
        record["eligibility_changes"] = {}
        for total in totals:
            moved = heads1[total] - heads0[total]
            if total in tax_totals:
                k = float(np.sum(hw * moved)) / expected_total
                if abs(k - 1) > tolerance:
                    problems.append(f"{total} moves by {k:.4f} per unit, not 1")
            else:
                # A household whose spending jumps by far more than it was
                # given has crossed an eligibility threshold rather than
                # counted the component twice, which adds exactly one more
                # per unit. Leave those households out, and count them.
                jumped = np.abs(moved - expected) > np.maximum(
                    ELIGIBILITY_JUMP_GBP, ELIGIBILITY_JUMP_FACTOR * expected
                )
                kept = float(np.sum(hw * expected * ~jumped))
                record["eligibility_changes"][total] = int(jumped.sum())
                if kept <= 0:
                    k = float("nan")
                    problems.append(
                        f"{total}: every perturbed household changed eligibility"
                    )
                else:
                    k = float(np.sum(hw * moved * ~jumped)) / kept
                    if k > 1 + tolerance:
                        problems.append(
                            f"{total} moves by {k:.4f} per unit, more than 1"
                        )
            record["coefficients"][total] = k
        for total in model_totals:
            if variable in partition.components(total, active):
                moved = _raw(sim, total, year).astype(np.float64) - model0[total]
                record["model_coefficients"][total] = (
                    float(np.sum(hw * moved)) / expected_total
                )
        if variable in declared:
            dc = declared[variable]
            moved = (
                _household(
                    sim,
                    _raw(sim, dc.contained_in, year),
                    variables[dc.contained_in].entity.key,
                )
                - container0[dc.contained_in]
            )
            k = float(np.sum(hw * moved)) / expected_total
            present = abs(k - 1) <= tolerance
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

    reset()
    heads_again = _totals_hh(sim, partition, year, partition_totals, active)
    reproduces = all(
        np.array_equal(heads_again[t], heads0[t]) for t in partition_totals
    )
    return {
        "status": "ran",
        "year": year,
        "tolerance": tolerance,
        "components": results,
        "double_counts": double_count_results,
        "reset_reproduces_baseline": bool(reproduces),
    }
