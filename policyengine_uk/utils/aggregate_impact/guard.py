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
  Each problem sets ``not_finite`` when a measurement behind it saw such a
  response in any of its households, since NaN times a weight of zero
  stays NaN, and ``not_finite_weighted`` when one of those households has
  weight. Its message adds ", or is not finite," in the second case;
  otherwise it keeps its finite text and adds that the head is not finite
  in households with no weight. A mediated response carries the same two
  flags for its first reading;
- the engine refuses NaN as an input, and an infinite amount is no level to
  hold, so the second held measurement holds another head at its baseline
  value in each unit where that head is not finite after the first point,
  and judges no household those units belong to. There a problem keeps
  every household it had. A head that may respond, whose slope was neither
  0 nor 1 and which the baseline hold did not show rising one for one,
  fails there as ``unconfirmed``: the check could not confirm whether it
  contains the component. Every other household gets both measurements.
  For each head it measured again, the component's result names those
  heads (``heads_not_held``) and counts the households
  (``households_not_held``); a problem does the same for the households
  that rest on the measurement the check could not make. A declared double
  count whose container's response is not finite fails: the check cannot
  show that the container still contains it;
- a head, a model total or a component that is not finite at baseline has
  no change to read where it is not finite, so the check cannot confirm it
  there. It names each such variable once, with the households, in
  ``not_finite_at_baseline``, which ``measure`` records as a failure of a
  ``finite:`` check, and it fails no component for it. No rule reads a
  head, or a model total, in the households where it, or one of its heads,
  is not finite at baseline. The engine refuses NaN as an input, so the
  check never sets such a value. To raise a component that is not finite
  at baseline, it sets each such unit to 0 and raises the others. The 0s
  change values only in the households that hold them, and it judges
  nothing there for that component. To hold a head that is not
  finite at baseline, it does not set the head at all: it leaves it to its
  formula. Wherever the head does not respond to the component, its
  formula gives it back the value the measurement holds it at (its
  baseline, NaN where it was NaN, or its value after the first point), so
  it is held there exactly and every other head reads what it would read
  with the head held. The check compares the head with that value, unit by
  unit and NaN matching only NaN, and judges the household only where they
  match. A problem in a household it could not judge stays, and names the
  head in ``heads_not_held_at_baseline``, beside ``heads_not_held``.

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
the baseline and requires it to match the first computation exactly, with
NaN matching only NaN in the same place.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Optional

import numpy as np

from .partition import Partition
from .privacy import MIN_CELL, count_text, small


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


def _not_finite_units(values) -> np.ndarray:
    """Units of a held layout (see ``_perturb``) whose value is not finite in
    any period."""
    if isinstance(values, list):
        return np.logical_or.reduce([~np.isfinite(v) for _, v in values])
    return ~np.isfinite(values)


def _held_values(at_first, baseline, units):
    """``at_first`` in its layout (see ``_perturb``), with each of ``units``
    at its ``baseline`` value in every period."""
    if isinstance(at_first, list):
        return [
            (month, np.where(units, start, value))
            for (month, value), (_, start) in zip(at_first, baseline)
        ]
    return np.where(units, baseline, at_first)


def _settable(values):
    """``values`` in its layout (see ``_perturb``), with each value that is not
    finite at 0: the engine refuses NaN as an input, and an infinite amount is
    no level to hold. Finite values keep every bit."""
    if isinstance(values, list):
        return [(month, np.where(np.isfinite(v), v, 0.0)) for month, v in values]
    return np.where(np.isfinite(values), values, 0.0)


def _households_text(households) -> str:
    """A count of households as messages give it (``count_text``); None is a
    small count that the published guard removed."""
    if households is None:
        return f"fewer than {MIN_CELL} households"
    return count_text(households, "households")


def problem_text(kind, head, component, households, not_finite=False, weighted=True):
    """What a problem of ``kind``, or a ``mediated`` response, says about
    ``head`` when ``component`` rises, in ``households`` households.

    A response behind it that is not finite in a household with weight adds
    the clause ", or is not finite,", and a containment then no longer
    concludes that the head contains the component. If every household where
    it is not finite has no weight (``weighted`` false), the text keeps its
    finite words for the households it counts and says so after the count.
    Finite responses keep their text word for word.
    """
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
        text = (
            f"the model's {head} moves by other than its heads{clause} when "
            f"{component} does"
        )
    text += f" in {_households_text(households)}"
    if not_finite and not weighted:
        text += ", and is not finite in households with no weight"
    return text


def _unheld_where(households, of_them=False) -> str:
    """The households where the check could not hold a head, as messages
    give them: none of them with weight reads "households with no weight"."""
    if households == 0:
        return "households with no weight"
    what = "of them" if of_them else "households"
    if households is None or small(households):
        return f"fewer than {MIN_CELL} {what}"
    return f"{households:,} {what}"


def _listed(names) -> tuple:
    """``names`` as a list in words, and how a relative clause refers to it."""
    if len(names) == 1:
        return names[0], "which is"
    return f"{', '.join(names[:-1])} and {names[-1]}", "one or more of which is"


def _unheld_words(heads, component, name=str, at_baseline=()) -> str:
    """The check could not hold ``heads``, which are not finite there once
    ``component`` rises, or ``at_baseline``, which it left to their formulas
    as they are not finite at baseline somewhere, and which moved there."""
    groups = []
    if heads:
        listed, which = _listed([name(v) for v in heads])
        groups.append(
            f"{listed}, {which} not finite there once {name(component)} rises"
        )
    if at_baseline:
        listed, which = _listed([name(v) for v in at_baseline])
        groups.append(
            f"{listed}, {which} not finite at baseline in some households and "
            f"moves there with {name(component)}"
        )
    return "the check could not hold " + ", and ".join(groups)


def not_held_note(component, head, heads, households, name=str) -> str:
    """What the check says when, measuring ``head`` again, it could not hold
    ``heads`` in ``households`` households (None: a small count that the
    published guard removed). ``name`` formats each variable's name."""
    return (
        f"in {_unheld_where(households)} {_unheld_words(heads, component, name)}, "
        f"so it measured {name(head)} again there only with the other heads at "
        "their baseline values"
    )


def not_finite_note(variable, households, name=str) -> str:
    """What the check says about ``variable``, not finite at baseline in
    ``households`` households with weight (None: a small count that the
    published guard removed)."""
    return (
        f"{name(variable)} is not finite at baseline in "
        f"{_unheld_where(households)}, so the counted-once check could not "
        "confirm it there"
    )


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
    at_baseline=(),
):
    """One failing (total, head, kind), with the households it fails in.

    ``nan`` marks the households where a measurement behind the problem saw
    a response that is not finite. ``unjudged`` marks the households of
    ``where`` that rest on a held measurement, which the check could not
    make there because it could not hold ``not_held`` (not finite once the
    component rises) or ``at_baseline`` (left to their formulas, as they are
    not finite at baseline somewhere, and moved there). The
    direct-effect step reads ``where``, ``nan`` and ``unjudged``, and
    ``counted_once`` drops them before it reports the result. The problem
    carries ``heads_not_held_at_baseline`` only when ``at_baseline`` names a
    head.
    """
    # Only households with weight count towards a published count.
    weighted = weights > 0
    count = int(np.count_nonzero(where & weighted))
    base = float(np.sum(weights * perturbed))
    share = float(np.sum(weights * where)) / base if base else 0.0
    not_finite = bool((where & nan).any())
    not_finite_weighted = bool((where & nan & weighted).any())
    unjudged = np.zeros_like(where) if unjudged is None else unjudged & where
    unheld = (
        int(np.count_nonzero(unjudged & weighted)) if not_held or at_baseline else 0
    )
    text = problem_text(kind, head, component, count, not_finite, not_finite_weighted)
    message = f"{total}: {text}"
    words = _unheld_words(list(not_held), component, at_baseline=list(at_baseline))
    if kind == "unconfirmed":
        message += (
            f" where {words}, so it could not confirm whether {head} contains "
            f"{component}"
        )
    elif not_held or at_baseline:
        message += (
            f" (in {_unheld_where(unheld, of_them=True)} {words}, so it could not "
            f"show that {head} responds only through other heads)"
        )
    out = {
        "total": total,
        "head": head,
        "kind": kind,
        "households": count,
        "share": share,
        "message": message,
        "not_finite": not_finite,
        "not_finite_weighted": not_finite_weighted,
        "heads_not_held": list(not_held),
    }
    if at_baseline:
        out["heads_not_held_at_baseline"] = list(at_baseline)
    out.update(households_not_held=unheld, where=where, nan=nan, unjudged=unjudged)
    return out


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
    unread: Optional[Mapping[str, np.ndarray]] = None,
    model_unread: Optional[np.ndarray] = None,
) -> dict:
    """Apply the counted-once rules, household by household, to one total.

    ``head_changes`` maps each head variable of the total to its change by
    household when 1 per unit was added to ``component`` (``expected`` by
    household); ``second_changes`` gives the changes when 2 per unit were
    added, where they were measured. ``unread`` marks, for a head, the
    households where its change cannot be read (it, or the component, is not
    finite at baseline there), and ``model_unread`` the same for the model's
    total. No rule judges a head there, nor the model's total where it or
    any head of the total cannot be read. A head's response, and the model
    total's coefficient, is its mean over the households where it can be
    read, and is left out where no household with weight can be.

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
    ``share`` (of the weight perturbed), ``message``, ``not_finite``,
    ``not_finite_weighted``, ``heads_not_held`` (empty here) and
    ``households_not_held`` (0 here), the households' mask ``where``, the
    mask ``nan`` of households whose judged response is not finite, and the
    mask ``unjudged`` (empty here).
    """
    allowed = set(allowed_readers)
    perturbed = expected > 0
    responses, problems, screens, own_problem = {}, [], [], None
    nowhere = np.zeros(len(expected), dtype=bool)
    unread = unread or {}

    def problem(head, kind, where, nan):
        return _problem(total, head, kind, component, where, weights, perturbed, nan)

    def mean_response(change, skip):
        """The mean change per unit added, over households not in ``skip``;
        None when ``skip`` leaves no household with weight to read."""
        added = float(np.sum(weights * np.where(skip, 0.0, expected)))
        if not added:
            return None if skip.any() else 0.0
        return float(np.sum(weights * np.where(skip, 0.0, change))) / added

    for variable, change in head_changes.items():
        skip = unread.get(variable, nowhere)
        response = mean_response(change, skip)
        if response is not None:
            responses[variable] = response
        slack = _slack(head_scales[variable])
        if variable == own_variable:
            off = ((np.abs(change - expected) > slack) | ~np.isfinite(change)) & ~skip
            if off.any():
                own_problem = problem(variable, "own_head", off, ~np.isfinite(change))
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
                linear = (
                    perturbed
                    & (np.abs(slope) > 2 * response_slack)
                    & ~containing
                    & ~skip
                )
                if linear.any():
                    screens.append(
                        problem(variable, "contains", linear, ~np.isfinite(slope))
                    )
            else:
                slope = change
                containing = perturbed & _contains(change, expected)
            # A response that is not finite fails wherever it is, as any
            # other head's does.
            containing = (containing | ~np.isfinite(slope)) & ~skip
            if containing.any():
                problems.append(
                    problem(variable, "contains", containing, ~np.isfinite(slope))
                )
        elif is_tax:
            moved = _moves(change, expected) & ~skip
            if moved.any():
                problems.append(problem(variable, "moves", moved, ~np.isfinite(change)))
        else:
            rises = _rises(change, slack) & ~skip
            if rises.any():
                problems.append(problem(variable, "rises", rises, ~np.isfinite(change)))
    partition_coefficient = float(sum(responses.values()))
    model_coefficient = None
    if model_change is not None:
        # The model's total cannot be read where it, or a head, cannot.
        skip = nowhere if model_unread is None else model_unread
        for variable in head_changes:
            skip = skip | unread.get(variable, nowhere)
        model_coefficient = mean_response(model_change, skip)
        heads_change = sum(head_changes.values())
        if declared_double_count:
            heads_change = heads_change + expected
        not_finite = ~np.isfinite(model_change) | ~np.isfinite(heads_change)
        beyond = np.abs(model_change - heads_change) > _slack(model_scale)
        mismatch = (beyond | not_finite) & ~skip
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


def _moved(sim, variable, year, layout) -> np.ndarray:
    """Households holding a unit where ``variable`` now differs from its value
    in ``layout`` (see ``_perturb``) in any period, NaN matching only NaN."""
    now, then = _capture(sim, [variable], year, layout)[variable], layout[variable]
    if isinstance(now, list):
        pairs = [(a, b) for (_, a), (_, b) in zip(now, then)]
    else:
        pairs = [(now, then)]
    differs = np.logical_or.reduce(
        [~((a == b) | (np.isnan(a) & np.isnan(b))) for a, b in pairs]
    )
    entity = sim.tax_benefit_system.variables[variable].entity.key
    return _household(sim, differs, entity) > 0


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


def _held_breaks(
    kind,
    where,
    expected,
    slack,
    first,
    second,
    slope_held,
    unjudged,
    unjudged_at_baseline=None,
):
    """Households of ``where`` where a held measurement that judged them
    still breaks ``kind`` (see ``still_breaks`` and ``breaks_on_slope``).

    ``slope_held`` is the slope with the other heads held at their values
    after the first point; it judges no household of ``unjudged``. ``first``
    and ``second``, with the other heads held at their baseline values,
    judge no household of ``unjudged_at_baseline``.
    """
    at_baseline = where
    if unjudged_at_baseline is not None:
        at_baseline = where & ~unjudged_at_baseline
    held_at_baseline = still_breaks(kind, at_baseline, expected, slack, first, second)
    judged = where & ~unjudged
    return held_at_baseline | breaks_on_slope(kind, judged, expected, slack, slope_held)


def _held_nan(kind, first, second, slope_held, unjudged, unjudged_at_baseline=None):
    """Households where a held measurement that judges ``kind`` (see
    ``_held_breaks``) saw a response that is not finite."""
    nan = ~np.isfinite(first)
    if kind == "contains" and second is not None:
        nan = nan | ~np.isfinite(second)
    if unjudged_at_baseline is not None:
        nan = nan & ~unjudged_at_baseline
    return nan | (~np.isfinite(slope_held) & ~unjudged)


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
    themselves are household by household (see ``judge_total``). The result
    carries ``not_finite_at_baseline`` only when a head, a model total or a
    component it raised is not finite at baseline: one entry for each, with
    the head's id and label (None for a variable that is no head), the
    households with weight where it is not finite, and a message.
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
    # Where the check sets a variable, it sets these values: the baseline,
    # with each value that is not finite at 0 (see the module docstring).
    settable = {variable: _settable(values) for variable, values in baseline.items()}
    # The households where each head, and each model total, has no change to
    # read: it is not finite there at baseline.
    unread = {v: ~np.isfinite(heads0[v]) for v in all_heads}
    free_heads = {v for v in all_heads if unread[v].any()}
    model_unread = {t: ~np.isfinite(model0[t]) for t in model_totals}
    # The same for each component the check raises, by the units it holds.
    blind_in = {}

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
                sum(values for _, values in baseline[variable])
                if monthly
                else baseline[variable]
            )
            # A unit that is not finite at baseline is never raised, and the
            # households holding one are judged for nothing: their readings
            # rest on the value the check sets there.
            broken = _not_finite_units(baseline[variable])
            nonzero = (year_values != 0) & ~broken
            zero_baseline = not bool(nonzero.any())
            mask = ~broken if zero_baseline else nonzero
            added = mask.astype(np.float64)
            blind = _household(sim, broken, entity) > 0
            if blind.any():
                blind_in[variable] = blind
            expected = np.where(blind, 0.0, _household(sim, added, entity))
            # Perturbed units in households with weight: a zero-weight record
            # adds nothing to any published figure.
            record["units"] = int(round(float(np.sum(expected[hw > 0]))))
            if not float(np.sum(hw * expected)) > 0:
                weighted_blind = bool((blind & (hw > 0)).any())
                record.update(
                    status="skipped",
                    detail=(
                        "the check could raise it only in households with no "
                        "weight or where it is not finite at baseline"
                        if weighted_blind
                        else "non-zero only in households with no weight"
                    ),
                )
                if weighted_blind and variable in declared:
                    dc = declared[variable]
                    double_count_results.append(
                        _unchecked_double_count(
                            dc,
                            f"the check could raise {variable} only in households "
                            "with no weight or where it is not finite at "
                            f"baseline, so it cannot show that {dc.contained_in} "
                            f"still contains {variable}",
                        )
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

            _perturb(sim, variable, year, settable, added, monthly, touched=touched)
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
                    sim, variable, year, settable, 2 * added, monthly, touched=touched
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
                    unread={v: unread[v] | blind for v in heads_of[total]},
                    model_unread=(
                        model_unread[total] | blind if total in model_unread else None
                    ),
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
                # The engine refuses NaN as an input, so the check sets no head
                # that is not finite at baseline: it leaves each to its formula,
                # and the measurement judges a household only where each came
                # out at the value it holds the heads at (see ``_moved``).
                fixed = [v for v in held if v not in free_heads]
                free = [v for v in held if v in free_heads]
                _perturb(
                    sim,
                    variable,
                    year,
                    settable,
                    added,
                    monthly,
                    hold=fixed,
                    touched=touched,
                )
                first = _head_arrays(sim, year, [head])[head] - heads0[head]
                moved_in = {v: _moved(sim, v, year, baseline) for v in free}
                second = None
                if any(
                    p["head"] == head and p["kind"] == "contains"
                    for p in problems + screens
                ):
                    _perturb(
                        sim,
                        variable,
                        year,
                        settable,
                        2 * added,
                        monthly,
                        hold=fixed,
                        touched=touched,
                    )
                    second = _head_arrays(sim, year, [head])[head] - heads0[head]
                    for v in free:
                        moved_in[v] = moved_in[v] | _moved(sim, v, year, baseline)
                for v in fixed:
                    _restore(sim, v, snapshot)
                # Second test: hold the other heads at their values after the
                # first point, and move the component on to the second. A head
                # gated by another head (h = c * (b > 0), with b a passport on c)
                # keeps its own slope here, though holding b at its baseline
                # switched it off above. The engine refuses NaN as an input, and
                # an infinite amount is no level to hold, so a unit where another
                # head is not finite after the first point keeps that head at its
                # baseline value, and this test judges no household the unit
                # belongs to.
                _perturb(sim, variable, year, settable, added, monthly, touched=touched)
                at_first = _capture(sim, held, year, baseline)
                head_first = _head_arrays(sim, year, [head])[head]
                held_at, unheld_in = {}, {}
                for v in fixed:
                    units = _not_finite_units(at_first[v])
                    held_at[v] = at_first[v]
                    if units.any():
                        held_at[v] = _held_values(at_first[v], baseline[v], units)
                        # Every household a unit belongs to, through the mapping
                        # that sums each head to households.
                        entity_key = definitions[v].entity.key
                        unheld_in[v] = _household(sim, units, entity_key) > 0
                _perturb(
                    sim,
                    variable,
                    year,
                    settable,
                    2 * added,
                    monthly,
                    hold=fixed,
                    held_at=held_at,
                    touched=touched,
                )
                slope_held = _head_arrays(sim, year, [head])[head] - head_first
                # A head left to its formula is held at its value after the
                # first point only where it stays there.
                moved_on = {v: _moved(sim, v, year, at_first) for v in free}
                for v in fixed:
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
                # The households each held measurement could not judge: the
                # second where a head it holds is not finite after the first
                # point or one left to its formula moved, the first (at the
                # baseline) where one left to its formula moved.
                unjudged_at_baseline = np.zeros(len(hw), dtype=bool)
                free_moved = {}
                for v in free:
                    unjudged_at_baseline = unjudged_at_baseline | moved_in[v]
                    unjudged = unjudged | moved_on[v]
                    if (moved_in[v] | moved_on[v]).any():
                        free_moved[v] = moved_in[v] | moved_on[v]
                either = unjudged | unjudged_at_baseline

                def unheld(where):
                    """The heads the check could not hold in ``where`` once the
                    component rises."""
                    return [v for v in not_held if bool((unheld_in[v] & where).any())]

                def unheld_free(where):
                    """The heads left to their formula that moved in ``where``."""
                    return [
                        v for v in free_moved if bool((free_moved[v] & where).any())
                    ]

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
                        unjudged_at_baseline,
                    )
                    # A held measurement clears no household it could not
                    # judge: there the problem rests on that measurement.
                    rests = p["where"] & either & ~breaks
                    direct = breaks | rests
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
                        # Both held measurements stay finite where they clear a
                        # household, so only the first reading can be not finite.
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
                                    p["kind"],
                                    first,
                                    second,
                                    slope_held,
                                    unjudged,
                                    unjudged_at_baseline,
                                ),
                                unheld(rests),
                                rests,
                                unheld_free(rests),
                            )
                        )
                # A linear response that was not one for one may hide a
                # containment that another head's response added to.
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
                        unjudged_at_baseline,
                    )
                    # Where a held measurement judged no household, the check
                    # could not confirm the reader there either way.
                    unconfirmed = screen["where"] & either & ~confirmed
                    nan = _held_nan(
                        "contains",
                        first,
                        second,
                        slope_held,
                        unjudged,
                        unjudged_at_baseline,
                    )
                    if confirmed.any():
                        not_held_there, rests, at_baseline_there = (), None, ()
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
                            not_held_there, rests, at_baseline_there = (
                                same["heads_not_held"],
                                same["unjudged"],
                                same.get("heads_not_held_at_baseline", ()),
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
                                at_baseline_there,
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
                                unheld_free(unconfirmed),
                            )
                        )
                problems = kept
            problems = [
                {k: v for k, v in p.items() if k not in ("where", "nan", "unjudged")}
                for p in problems
            ]
            record["mediated"] = mediated
            record["heads_held_skipped"] = bool(record["heads_not_held"]) or any(
                "heads_not_held_at_baseline" in p for p in problems
            )
            if variable in declared:
                double_count_results.append(
                    _double_count_row(
                        declared[variable],
                        heads1[own] - heads0[own],
                        expected,
                        # The households where the container's change can be read.
                        ~(unread[own] | blind),
                        hw,
                        heads0[own],
                    )
                )
            if problems:
                record.update(
                    status="fail",
                    problems=problems,
                    detail="; ".join(p["message"] for p in problems),
                )
            else:
                # A pass still says where the second held measurement could
                # not hold a head, in the words the report uses.
                record["detail"] = "; ".join(
                    not_held_note(
                        variable, head, heads, record["households_not_held"][head]
                    )
                    for head, heads in record["heads_not_held"].items()
                )
            results.append(record)
            _restore(sim, variable, snapshot)
    finally:
        for variable in sorted(touched):
            _restore(sim, variable, snapshot)

    discard_formula_results(sim)
    heads_again = _head_arrays(sim, year, all_heads)
    # NaN matches NaN in the same place, and nothing else.
    reproduces = all(
        np.array_equal(heads_again[v], heads0[v], equal_nan=True) for v in all_heads
    )
    result = {
        "status": "ran",
        "year": year,
        "tolerance": tolerance,
        "components": results,
        "double_counts": double_count_results,
        "reset_reproduces_baseline": bool(reproduces),
    }
    # Each variable the check could not read somewhere, named once: the heads,
    # the model totals, then the other components it raised.
    where_not_finite = {
        **{v: unread[v] for v in all_heads if unread[v].any()},
        **{t: model_unread[t] for t in model_totals if model_unread[t].any()},
    }
    for variable, blind in blind_in.items():
        where_not_finite.setdefault(variable, blind)
    if where_not_finite:
        result["not_finite_at_baseline"] = []
        for variable, households in where_not_finite.items():
            head = head_by_variable.get(variable)
            count = int(np.count_nonzero(households & (hw > 0)))
            result["not_finite_at_baseline"].append(
                {
                    "variable": variable,
                    "head": None if head is None else head.id,
                    "label": None if head is None else head.label,
                    "households": count,
                    "message": not_finite_note(variable, count),
                }
            )
    return result


def _double_count_row(dc, change, expected, readable, weights, scale) -> dict:
    """Whether the container of a declared double count still moves by exactly
    what was added to it, in each household where its ``change`` can be read
    (``readable``)."""
    variable, container = dc.variable, dc.contained_in
    base = float(np.sum(weights * np.where(readable, expected, 0.0)))
    if not base > 0:
        return _unchecked_double_count(
            dc,
            f"{container} is not finite at baseline in every household with "
            f"weight where the check raised {variable}, so it cannot show that "
            f"{container} still contains {variable}",
        )
    k = float(np.sum(weights * np.where(readable, change, 0.0))) / base
    finite = bool(np.isfinite(change[readable]).all())
    present = finite and not bool(
        ((np.abs(change - expected) > _slack(scale)) & readable).any()
    )
    row = {
        "variable": variable,
        "contained_in": container,
        "coefficient": k,
        "issue": dc.issue,
        "status": "pass" if present else "fail",
        "not_finite": not finite,
        "detail": ""
        if present
        else (
            f"{container} moves by {k:.4f} per unit of {variable}: the model no "
            "longer counts it twice, so remove the declaration and give it its "
            "own head"
        ),
    }
    if not finite:
        # Not a stale declaration: the check cannot tell.
        row["detail"] = (
            f"{container} is not finite when {variable} rises, so the check "
            f"cannot show that {container} still contains {variable}"
        )
    return row


def _unchecked_double_count(dc, detail) -> dict:
    """A declared double count the check could not judge anywhere: a
    container or component not finite at baseline wherever it would read it.
    It is skipped, not passed, and a ``finite:`` check names the cause."""
    return {
        "variable": dc.variable,
        "contained_in": dc.contained_in,
        "coefficient": None,
        "issue": dc.issue,
        "status": "skipped",
        "not_finite": False,
        "detail": detail,
    }
