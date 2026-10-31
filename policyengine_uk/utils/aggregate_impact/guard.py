"""The counted-once check: no head silently contains another head's component.

For each component of a partition total, the check adds 1 to every unit
where the component is non-zero (to every unit, if it is zero everywhere),
recomputes every head of the totals it belongs to, and reads each head's
change household by household (see ``judge_total``):

- the component's own head (itself, or the head a declared double count is
  contained in) must rise by exactly what was added;
- no other tax head may move, and no other benefit may rise. Means tests may
  lower other benefits when one rises (Pension Credit falls as State Pension
  rises), but a benefit that rises with another either contains it or pays
  more to people with more income. Households are judged one by one, so a
  fall elsewhere cannot offset a rise;
- a head that declares a read of the component's head (``reads`` in the
  partition), and any benefit when the component was zero for everyone (so
  that perturbing it makes new recipients, whom passporting can reach), may
  respond, but not with a slope of exactly 1. The check adds 2 as well and
  fails any household where such a head rose between the two points by
  exactly what was added; a step such as a passport moves it by the same
  amount at both, so its slope is 0;
- the model's own total must move, household by household, by what its
  heads moved, plus the addition again for a declared double count. This
  catches a total whose formula adds a component twice even while that
  component is zero;
- a head that breaks one of the rules above, and a head that may respond
  whose slope is neither 0 nor 1, is measured again twice: with every other
  head held at its baseline value, and with every other head held at its
  value after the first point while the component moves on to the second.
  It fails in households where either still shows the response (a move, a
  rise, a slope of 1). A head can respond to the component through another
  head without containing it: Incapacity Benefit reduces Carer's Allowance
  (overlapping benefits), and Universal Credit, which in the model counts
  Carer's Allowance as income but not Incapacity Benefit (issue #2424),
  rises by what Carer's Allowance lost. Holding the other heads removes
  that route. The second hold keeps a head's own response where another
  head gates it: in ``h = c * (b > 0)`` with ``b = 40 * (c > 0)``, holding
  ``b`` at its baseline switches ``h`` off, but holding it at its perturbed
  value keeps ``h``'s slope of 1. A head that contains another head is still
  found when that other head is the one perturbed. Responses through other
  heads are reported as ``mediated``, with the other heads that moved in
  those households: candidates for the route, not each shown to carry it;
- a response that is not finite (infinite or NaN) breaks each rule above,
  for every head and for the model's total, and in both held measurements.
  The second measurement does not run when another head's response is not
  finite, since it would hold that head there; it then clears no problem
  and confirms no screen. A declared double count whose container's
  response is not finite fails: the check cannot show that the container
  still contains it.

What it cannot see: a head that adds a component back while tapering it away
pound for pound (``max(0, a - c) + c``) does not move at the margin, so it is
indistinguishable from a flat benefit that ignores the component. Such a
head counts the component twice wherever the taper binds; only reading its
formula, or a test that sets the component's level, can find it. Likewise a
benefit that contains the component while, in every household perturbed, a
fall carried by another head offsets or outweighs its rise shows no rise and
is not measured again; in any household without that route its rise shows.

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
from .privacy import count_text


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


class _InputSnapshot(dict):
    """Original arrays with guard-private provenance; mapping entries stay arrays."""

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
    """Copy actual registered input slots before any synthetic write."""
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
    """Copy original input arrays and registered origin/branch placement.

    Formula caches are discarded first. The provenance sidecar is an attribute,
    not a mapping entry, so existing callers still receive variable/array pairs.
    """
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
    # Plain mappings remain supported when their registered values agree with
    # actual original storage. Never infer origin from a post-probe cache.
    for name in set(snapshot) & SUPPLIED_INPUT_VARIABLES:
        for period, value in snapshot[name]:
            if not any(
                saved_period == period and np.array_equal(saved_value, value)
                for _, saved_period, saved_value, _ in origins.get(name, ())
            ):
                raise ValueError("Plain input snapshot has no matching original slot")
    return _InputSnapshot(snapshot, owner=sim, origins=origins)


def _set_guard_value(sim, variable, period, value, touched=None):
    """A synthetic value is not a new user declaration of a legacy input."""
    from policyengine_uk.utils.supplied_inputs import (
        SUPPLIED_INPUT_VARIABLES,
        set_model_value,
    )

    if touched is not None:
        touched.add(variable)
    if variable in SUPPLIED_INPUT_VARIABLES:
        set_model_value(sim, variable, period, value)
    else:
        # Keep other UK provenance hooks, including CGT, on their existing path.
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
    # Simulation.delete_arrays would purge visible ancestor/default branches in
    # this holder too. Only remove the current branch's synthetic slots here.
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
    """Each variable's values summed to households."""
    definitions = sim.tax_benefit_system.variables
    return {
        v: _household(sim, _raw(sim, v, year), definitions[v].entity.key)
        for v in variables
    }


# Level comparisons allow this many pounds plus this share of the head's
# own value: the model stores values as float32. Containment and undeclared
# tax movement use the response and perturbation (see ``_response_slack``
# and ``_moves``).
ABSOLUTE_SLACK_GBP = 0.02
RELATIVE_SLACK = 2e-6


def _slack(scale: np.ndarray) -> np.ndarray:
    return ABSOLUTE_SLACK_GBP + RELATIVE_SLACK * np.abs(scale)


def _response_slack(response: np.ndarray, expected: np.ndarray) -> np.ndarray:
    """Scale the £1 response allowance by the amount added, not the head level.

    A flat reader must never be close to one for one, even for a small
    perturbation or a large baseline. The relative term allows rounding in
    the response itself; two-point differences use twice this allowance.
    """
    return ABSOLUTE_SLACK_GBP * np.abs(expected) + RELATIVE_SLACK * np.abs(response)


def _moves(
    response: np.ndarray, expected: np.ndarray, allowances: int = 1
) -> np.ndarray:
    """Households where an undeclared tax head's response counts as movement.

    A response moves when it exceeds ``allowances`` response allowances, or
    when it is not finite: an infinite response gets an infinite allowance,
    and NaN compares false with any allowance.
    """
    beyond = np.abs(response) > allowances * _response_slack(response, expected)
    return beyond | ~np.isfinite(response)


def _contains(
    response: np.ndarray, expected: np.ndarray, allowances: int = 1
) -> np.ndarray:
    """Households where a reader's response counts as containing the component.

    A response contains it when it is within ``allowances`` response
    allowances of what was added, or when it is not finite: NaN compares
    false with any allowance.
    """
    close = np.abs(response - expected) <= allowances * _response_slack(
        response, expected
    )
    return close | ~np.isfinite(response)


def _rises(response: np.ndarray, slack: np.ndarray) -> np.ndarray:
    """Households where a benefit's response counts as a rise: beyond
    ``slack``, or not finite, whichever way it points."""
    return (response > slack) | ~np.isfinite(response)


def _finite(values) -> bool:
    """Whether a held layout (see ``_perturb``) holds only finite values."""
    if isinstance(values, list):
        return all(bool(np.isfinite(v).all()) for _, v in values)
    return bool(np.isfinite(values).all())


def _containment_text(head, component, finite=True):
    """A containment problem's text; ``finite`` is False when a response in
    its households is not finite."""
    if finite:
        return f"{head} rises one for one with {component}, so it contains it,"
    return f"{head} rises one for one with {component}, or is not finite,"


def _problem(total, head, kind, where, text, weights, perturbed):
    """One failing (total, head, kind), with the households it fails in.

    ``where`` and ``text`` are kept for the direct-effect step and dropped
    before the result is reported.
    """
    # Only households with weight count towards a published count.
    count = int(np.count_nonzero(where & (weights > 0)))
    base = float(np.sum(weights * perturbed))
    share = float(np.sum(weights * where)) / base if base else 0.0
    return {
        "total": total,
        "head": head,
        "kind": kind,
        "households": count,
        "share": share,
        "message": f"{total}: {text} in {count_text(count, 'households')}",
        "where": where,
        "text": text,
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
    """Apply the counted-once rules, household by household, to one total.

    ``head_changes`` maps each head variable of the total to its change by
    household when 1 per unit was added to ``component`` (``expected`` by
    household); ``second_changes`` gives the changes when 2 per unit were
    added, where they were measured.

    - The component's own head must change by exactly ``expected`` in every
      household.
    - A tax head may not move in any household; a spending head may not rise
      in any household.
    - A head that declares a read of the component's head, and any spending
      head when the component is zero for everyone, may respond, except one
      for one: a household where the head's slope between the two points is
      exactly what was added contains the component.
    - The model's own total must change, in every household, by what its
      heads changed plus ``expected`` again for a declared double count.
    - A response that is not finite breaks each of these rules, in every
      household where it occurs.

    Returns per-unit responses (for reports) and a list of problems, each a
    mapping with ``total``, ``head``, ``kind``, ``households`` (count),
    ``share`` (of the weight perturbed), ``message`` and the households'
    mask ``where``.
    """
    added = float(np.sum(weights * expected))
    allowed = set(allowed_readers)
    perturbed = expected > 0
    responses, problems, screens, own_problem = {}, [], [], None

    def problem(head, kind, where, text):
        return _problem(total, head, kind, where, text, weights, perturbed)

    def containment(head, response=None, where=None):
        finite = response is None or bool(np.isfinite(response[where]).all())
        return _containment_text(head, component, finite)

    for variable, change in head_changes.items():
        responses[variable] = float(np.sum(weights * change)) / added if added else 0.0
        slack = _slack(head_scales[variable])
        if variable == own_variable:
            off = (np.abs(change - expected) > slack) | ~np.isfinite(change)
            if off.any():
                own_problem = problem(
                    variable,
                    "own_head",
                    off,
                    f"{variable} does not move by exactly what was added to {component}",
                )
            continue
        reader = variable in allowed or (zero_baseline and not is_tax)
        if reader:
            if second_changes is not None:
                # The slope between the two points: 1 for a head that contains
                # the component, 0 for a step such as a passport, whatever
                # else moved the head at the first point.
                slope = second_changes[variable] - change
                response_slack = _response_slack(slope, expected)
                containing = perturbed & _contains(slope, expected, 2)
                # Another head's response can add to a containing head's
                # slope, so any other linear response is measured again with
                # the other heads held.
                linear = perturbed & (np.abs(slope) > 2 * response_slack) & ~containing
                if linear.any():
                    screens.append(
                        problem(variable, "contains", linear, containment(variable))
                    )
            else:
                slope = change
                containing = perturbed & _contains(change, expected)
            # A response that is not finite fails wherever it is, as any
            # other head's does.
            containing = containing | ~np.isfinite(slope)
            if containing.any():
                problems.append(
                    problem(
                        variable,
                        "contains",
                        containing,
                        containment(variable, slope, containing),
                    )
                )
        elif is_tax:
            moved = _moves(change, expected)
            if moved.any():
                problems.append(
                    problem(
                        variable,
                        "moves",
                        moved,
                        f"{variable} moves when {component} does",
                    )
                )
        else:
            rises = _rises(change, slack)
            if rises.any():
                finite = bool(np.isfinite(change[rises]).all())
                problems.append(
                    problem(
                        variable,
                        "rises",
                        rises,
                        f"{variable} rises when {component} does"
                        if finite
                        else f"{variable} rises, or is not finite, when {component} does",
                    )
                )
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
            moves = "moves by other than its heads"
            if not_finite.any():
                moves += ", or is not finite,"
            problems.append(
                problem(
                    total,
                    "model_total",
                    mismatch,
                    f"the model's {total} {moves} when {component} does",
                )
            )
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
    """Add ``added`` to ``variable``, holding each of ``hold`` fixed.

    Held variables keep their values in ``held_at`` (by default the
    baseline), in the same layout: an array for a yearly variable, a list
    of (month, array) for a monthly one.
    """
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
    """Each variable's current values, in ``layout``'s form (see ``_perturb``)."""
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
    """Households of ``where`` whose head's slope, with the other heads held at
    their values after the first point, breaks ``kind``."""
    if kind == "contains":
        return where & _contains(slope, expected, allowances=2)
    if kind == "rises":
        return where & _rises(slope, 2 * slack)
    if kind == "moves":
        return where & _moves(slope, expected, allowances=2)
    return where


def still_breaks(kind, where, expected, slack, first, second=None):
    """Households of ``where`` whose head breaks ``kind`` with other heads held.

    ``first`` (and ``second``, for a containment judged on a slope) are the
    head's changes when the component was raised by ``expected`` (and twice
    that) with every other head at its baseline value.
    """
    if kind == "contains":
        if second is not None:
            return where & _contains(second - first, expected, allowances=2)
        return where & _contains(first, expected)
    if kind == "rises":
        return where & _rises(first, slack)
    if kind == "moves":
        return where & _moves(first, expected)
    return where


def _held_breaks(kind, where, expected, slack, first, second, slope_held, unrun):
    """Households of ``where`` where either held measurement still breaks
    ``kind`` (see ``still_breaks`` and ``breaks_on_slope``).

    ``slope_held`` is the slope with the other heads held at their values
    after the first point, or None where that test did not run, which gives
    ``unrun``.
    """
    held_at_baseline = still_breaks(kind, where, expected, slack, first, second)
    if slope_held is None:
        return held_at_baseline | unrun
    return held_at_baseline | breaks_on_slope(kind, where, expected, slack, slope_held)


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
    """Perturb each component (or those in ``variables_to_check``).

    ``tolerance`` is kept for reports of per-unit responses; the verdicts
    themselves are household by household (see ``judge_total``).
    """
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
            # Perturbed units in households with weight: a zero-weight record
            # adds nothing to any published figure.
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
            needed = list(dict.fromkeys(v for t in in_totals for v in heads_of[t]))
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
            # A head that may respond (a declared reader, or any benefit when the
            # component was zero for everyone) is checked for containment at a
            # second point, which tells a slope of 1 from a step.
            may_respond = {
                v
                for total in in_totals
                for v in heads_of[total]
                if v != own
                and (
                    v in readers_of[total]
                    or (zero_baseline and not partition.is_tax_total(total))
                )
            }
            heads2 = None
            if may_respond:
                _perturb(
                    sim, variable, year, baseline, 2 * added, monthly, touched=touched
                )
                heads2 = _head_arrays(sim, year, sorted(may_respond))
            problems, screens = [], []
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
                    model_change=(
                        model1[total] - model0[total] if total in model1 else None
                    ),
                    model_scale=model0.get(total),
                    allowed_readers=readers_of[total],
                    second_changes=None
                    if heads2 is None
                    else {v: heads2[v] - heads0[v] for v in heads2},
                )
                record["coefficients"][total] = verdict["coefficient"]
                if verdict["model_coefficient"] is not None:
                    record["model_coefficients"][total] = verdict["model_coefficient"]
                # The report keeps a response that is not finite too.
                record["responses"][total] = {
                    v: r
                    for v, r in verdict["responses"].items()
                    if not abs(r) <= tolerance
                }
                problems += verdict["problems"]
                screens += verdict["screens"]
                # The double count's own check below reports a declared double
                # count whose container no longer moves, or is not finite.
                if verdict["own_problem"] and variable not in declared:
                    problems.append(verdict["own_problem"])
            # Measure each head that broke a rule again with every other head
            # held at its baseline value: a response carried by another head
            # (the head reading that head's change) is not containment.
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
                    p["head"] == head and p["kind"] == "contains"
                    for p in problems + screens
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
                # Second test: hold the other heads at their values after the
                # first point, and move the component on to the second. A head
                # gated by another head (h = c * (b > 0), with b a passport on c)
                # keeps its own slope here, though holding b at its baseline
                # switched it off above. It holds them only at finite values:
                # the engine refuses NaN as an input, and an infinite amount is
                # no level to hold. When another head's response is not finite
                # the test does not run (slope_held stays None).
                _perturb(sim, variable, year, baseline, added, monthly, touched=touched)
                at_first = _capture(sim, held, year, baseline)
                slope_held = None
                if all(_finite(at_first[v]) for v in held):
                    head_first = _head_arrays(sim, year, [head])[head]
                    _perturb(
                        sim,
                        variable,
                        year,
                        baseline,
                        2 * added,
                        monthly,
                        hold=held,
                        held_at=at_first,
                        touched=touched,
                    )
                    slope_held = _head_arrays(sim, year, [head])[head] - head_first
                    for v in held:
                        _restore(sim, v, snapshot)
                slack = _slack(heads0[head])
                kept = []
                for p in problems:
                    if p["head"] != head or p["kind"] not in DIRECT_KINDS:
                        kept.append(p)
                        continue
                    # A measurement that did not run clears no household.
                    direct = _held_breaks(
                        p["kind"],
                        p["where"],
                        expected,
                        slack,
                        first,
                        second,
                        slope_held,
                        unrun=p["where"],
                    )
                    cleared = p["where"] & ~direct
                    if cleared.any():
                        # The other heads that moved there: candidates for the
                        # route, not each shown to carry it.
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
                        mediated.append(
                            {
                                "total": p["total"],
                                "head": head,
                                "kind": p["kind"],
                                "households": int(np.count_nonzero(cleared & (hw > 0))),
                                "via": via,
                            }
                        )
                    if direct.any():
                        kept.append(
                            _problem(
                                p["total"],
                                head,
                                p["kind"],
                                direct,
                                p["text"],
                                hw,
                                perturbed_units,
                            )
                        )
                # A linear response that was not one for one may hide a
                # containment that another head's response added to.
                for screen in screens:
                    if screen["head"] != head:
                        continue
                    # A measurement that did not run confirms no household.
                    direct = _held_breaks(
                        "contains",
                        screen["where"],
                        expected,
                        slack,
                        first,
                        second,
                        slope_held,
                        unrun=np.zeros_like(screen["where"]),
                    )
                    if not direct.any():
                        continue
                    finite = all(
                        bool(np.isfinite(measured[direct]).all())
                        for measured in (first, second, slope_held)
                        if measured is not None
                    )
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
                        direct = direct | same["where"]
                        finite = finite and same["text"] == screen["text"]
                    kept.append(
                        _problem(
                            screen["total"],
                            head,
                            "contains",
                            direct,
                            _containment_text(head, variable, finite),
                            hw,
                            perturbed_units,
                        )
                    )
                problems = kept
            problems = [
                {k: v for k, v in p.items() if k not in ("where", "text")}
                for p in problems
            ]
            record["mediated"] = mediated
            if variable in declared:
                dc = declared[variable]
                container_change = heads1[own] - heads0[own]
                k = float(np.sum(hw * container_change)) / float(np.sum(hw * expected))
                finite = bool(np.isfinite(container_change).all())
                present = finite and not bool(
                    (np.abs(container_change - expected) > _slack(heads0[own])).any()
                )
                row = {
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
                if not finite:
                    # Not a stale declaration: the check cannot tell.
                    row.update(
                        not_finite=True,
                        detail=(
                            f"{dc.contained_in} is not finite when {variable} "
                            "rises, so the check cannot show that it still "
                            f"contains {variable}"
                        ),
                    )
                double_count_results.append(row)
            if problems:
                record.update(
                    status="fail",
                    problems=problems,
                    detail="; ".join(p["message"] for p in problems),
                )
            results.append(record)
            _restore(sim, variable, snapshot)
    finally:
        for variable in sorted(touched):
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
