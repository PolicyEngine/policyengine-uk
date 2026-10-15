"""Compare a base and a head measurement.

The comparison fails when either side did not run, when they ran on
different data, when the head has a non-finite figure, when a check the base
ran is missing from the head, or when the head fails a check in a scope (a
year) where the base passes it. It reports, without failing, checks that
fail in the same scopes on both sides (pre-existing) and moves above the
flag thresholds.
"""

from __future__ import annotations

import math
from typing import Iterable, Mapping, Optional

import numpy as np

from . import TOOL_SCHEMA
from .privacy import HIDDEN_KEY, MIN_CELL, small
from .spec import Spec, fiscal_year_label

# Failing these on the head blocks the change whatever the base did: a
# non-finite or crashed result cannot be compared at all.
ALWAYS_BLOCKING_PREFIXES = ("finite:", "weights:")

# Every head measurement must have run these.
REQUIRED_CHECKS = (
    "closure",
    "finite:metrics",
    "weights:person",
    "weights:benunit",
    "weights:household",
)

FLAG_KIND_BY_SECTION = {
    "reforms": "reform_gbp",
    "reform_targets": "reform_gbp",
}

DECILES = tuple(range(1, 11))


def _metric_map(result: Optional[Mapping]) -> dict:
    if not result or result.get("status") != "ok":
        return {}
    return {m["id"]: m for m in result.get("metrics", [])}


def _check_map(result: Optional[Mapping]) -> dict:
    if not result or result.get("status") != "ok":
        return {}
    return {c["id"]: c for c in result.get("checks", [])}


def _finite(value) -> bool:
    return (
        value is not None and isinstance(value, (int, float)) and math.isfinite(value)
    )


def classify_check(
    base_status: Optional[str],
    head_status: Optional[str],
    blocking: bool,
    base_failing: Iterable[str] = (),
    head_failing: Iterable[str] = (),
) -> str:
    """How a check's outcome on the head relates to the base.

    ``base_failing`` and ``head_failing`` are the scopes (years) each side
    failed in. A failure is pre-existing only if the base fails in every
    scope the head fails in; a newly failing year is a regression.

    Returns one of: ``pass``, ``regression``, ``pre_existing``, ``fixed``,
    ``new_warning``, ``warning``, ``skipped``, ``removed``.
    """
    if head_status is None:
        return "removed"
    if head_status == "skipped":
        return "skipped"
    if head_status == "pass":
        return "fixed" if base_status in ("fail", "warn") else "pass"
    if head_status == "warn":
        return "warning" if base_status == "warn" else "new_warning"
    # head failed
    if blocking or base_status != "fail":
        return "regression"
    if set(head_failing) - set(base_failing):
        return "regression"
    return "pre_existing"


def _is_suppressed(metrics: Mapping, metric_id: str, key: str) -> bool:
    metric = metrics.get(metric_id)
    return metric is not None and key in metric.get("suppressed", ())


def _published(metrics: Mapping, metric_id: str, key: str):
    metric = metrics.get(metric_id)
    return None if metric is None else metric["values"].get(key)


def _protected_ids(base_hidden, head_hidden, key: str) -> set:
    """Totals protected in ``key`` because they contain a suppressed head."""
    out = set()
    for hidden in (base_hidden, head_hidden):
        for cell in (hidden or {}).get("contains", {}):
            metric_id, _, year = cell.rpartition("|")
            if year == key:
                out.add(metric_id)
    return out


def private_delta(
    metric_id: str,
    key: str,
    base: Mapping,
    head: Mapping,
    base_hidden: Optional[Mapping],
    head_hidden: Optional[Mapping],
):
    """A protected total's exact change, or None when it could reveal a head.

    A total rounded (or suppressed) because it contains a suppressed head is
    published only approximately. Its exact change, read from the raw values
    in each side's private detail, is published when every suppressed head
    inside it is unchanged between base and head: the change is then the sum
    of the published heads' changes and reveals nothing more. Otherwise, or
    without both sides' private detail, it is None.
    """
    if not base_hidden or not head_hidden:
        return None
    cell = f"{metric_id}|{key}"
    b = base_hidden["values"].get(cell, _published(base, metric_id, key))
    h = head_hidden["values"].get(cell, _published(head, metric_id, key))
    if not (_finite(b) and _finite(h)):
        return None
    inside = set(base_hidden["contains"].get(cell, ())) | set(
        head_hidden["contains"].get(cell, ())
    )
    # A head suppressed on one side only: an exact change would show what the
    # few records on the suppressed side add up to (Sol re-review 4).
    for metric_id_ in inside | {metric_id}:
        if _is_suppressed(base, metric_id_, key) != _is_suppressed(
            head, metric_id_, key
        ):
            return None
    for head_id in inside:
        hk = f"{head_id}|{key}"
        b_raw = base_hidden["values"].get(hk, _published(base, head_id, key))
        h_raw = head_hidden["values"].get(hk, _published(head, head_id, key))
        if not (_finite(b_raw) and _finite(h_raw)) or b_raw != h_raw:
            return None
    return h - b


def compare_metrics(
    base: Mapping,
    head: Mapping,
    spec: Spec,
    years,
    base_hidden: Optional[Mapping] = None,
    head_hidden: Optional[Mapping] = None,
) -> tuple:
    rows, flags = [], []
    ids = list(dict.fromkeys(list(head) + list(base)))
    for metric_id in ids:
        head_metric, base_metric = head.get(metric_id), base.get(metric_id)
        template = head_metric or base_metric
        row = {
            "id": metric_id,
            "label": template["label"],
            "section": template["section"],
            "group": template.get("group"),
            "kind": template["kind"],
            "unit": template.get("unit"),
            "values": {},
            # A figure measured on one side only is a change, never "no change".
            "changed": not (head_metric and base_metric),
            "only_in": None
            if head_metric and base_metric
            else ("head" if head_metric else "base"),
        }
        kind = FLAG_KIND_BY_SECTION.get(template["section"], template["kind"])
        threshold = spec.threshold(kind)
        for year in years:
            key = str(year)
            b = base_metric["values"].get(key) if base_metric else None
            h = head_metric["values"].get(key) if head_metric else None
            # A figure from too few records is published as None, and a total
            # containing one is rounded (privacy.py, measure.protect_totals).
            b_hidden = key in (base_metric or {}).get("suppressed", ())
            h_hidden = key in (head_metric or {}).get("suppressed", ())
            protected_total = (
                key in (base_metric or {}).get("rounded", ())
                or key in (head_metric or {}).get("rounded", ())
                or (
                    (b_hidden or h_hidden)
                    and metric_id in _protected_ids(base_hidden, head_hidden, key)
                )
            )
            if protected_total and base_metric and head_metric:
                delta = private_delta(
                    metric_id, key, base, head, base_hidden, head_hidden
                )
            elif b_hidden or h_hidden:
                # A head from fewer than 10 records: its change is too.
                delta = None
            else:
                delta = h - b if _finite(b) and _finite(h) else None
            row["values"][key] = {
                "base": b,
                "head": h,
                "delta": delta,
                "base_suppressed": b_hidden,
                "head_suppressed": h_hidden,
                # Published levels are approximate and the exact change is
                # withheld: a suppressed head inside the total changed, or the
                # private detail was not available.
                "rounded": bool(protected_total and delta is None),
            }
            if (delta is not None and delta != 0) or (
                base_metric and head_metric and b_hidden != h_hidden
            ):
                row["changed"] = True
            if (
                protected_total
                and delta is None
                and base_metric
                and head_metric
                and b != h
            ):
                row["changed"] = True
            if (
                delta is not None
                and threshold is not None
                and _finite(b)
                and threshold.exceeded(b, b + delta)
            ):
                flags.append(
                    {
                        "id": metric_id,
                        "label": template["label"],
                        "section": template["section"],
                        "kind": template["kind"],
                        "year": year,
                        "base": b,
                        "head": h,
                        "delta": delta,
                        "limit": threshold.limit(b),
                    }
                )
        rows.append(row)
    return rows, flags


def _match(base_ids: np.ndarray, head_ids: np.ndarray) -> Optional[np.ndarray]:
    """Indices into head arrays that line up with base households, or None.

    The two sides must hold exactly the same households, each once.
    """
    base_ids, head_ids = np.asarray(base_ids), np.asarray(head_ids)
    if base_ids.shape != head_ids.shape:
        return None
    if np.array_equal(base_ids, head_ids):
        if len(np.unique(base_ids)) != len(base_ids):
            return None
        return np.arange(len(head_ids))
    if len(np.unique(base_ids)) != len(base_ids) or len(np.unique(head_ids)) != len(
        head_ids
    ):
        return None
    order = np.argsort(head_ids, kind="stable")
    positions = np.clip(np.searchsorted(head_ids[order], base_ids), 0, len(order) - 1)
    matched = order[positions]
    if not np.array_equal(head_ids[matched], base_ids):
        return None
    return matched


def decile_impacts(base_households: Mapping, head_households: Mapping, years) -> tuple:
    """Household-matched income changes within the base run's deciles.

    For each year and decile d of the base run: the mean change in the income
    variable per household and the change relative to the decile's base
    income, both weighted by the base household weights; plus the shares of
    people (household weight times household size) whose household gains or
    loses more than £1 a year.

    Small cells (privacy.py, Sol re-review 3 of #2335):

    - A row where fewer than ``MIN_CELL`` households with weight change at
      all publishes no change: its mean change times the decile's weight
      would give those households' change back.
    - No row publishes its households' weight or base income, and changes
      are rounded to what the comment shows (£1 and 0.1%). Otherwise the
      "all" row's base income, from its mean change over its relative
      change, times the published household count, would rebuild the
      household income total that ``measure.protect_totals`` rounds. With
      0.1%, a 20% change pins the base to about ±0.25%, some £3.5bn of a
      £1.4tn total (Sol re-review 4: 0.01% left ±£420m).
    """
    impacts, notes = {}, []
    for year in years:
        key = str(year)
        b, h = base_households.get(key), head_households.get(key)
        if b is None or h is None:
            notes.append(f"{fiscal_year_label(year)}: household detail missing")
            continue
        matched = _match(np.asarray(b["household_id"]), np.asarray(h["household_id"]))
        if matched is None:
            notes.append(f"{fiscal_year_label(year)}: base and head households differ")
            continue
        weight = np.asarray(b["household_weight"], dtype=np.float64)
        head_weight = np.asarray(h["household_weight"], dtype=np.float64)[matched]
        if not np.array_equal(weight, head_weight):
            notes.append(
                f"{fiscal_year_label(year)}: household weights changed; decile "
                "changes use the base weights"
            )
        people = np.asarray(b["household_count_people"], dtype=np.float64)
        decile = np.asarray(b["decile"])
        base_income = np.asarray(b["income"], dtype=np.float64)
        change = np.asarray(h["income"], dtype=np.float64)[matched] - base_income
        rows = []
        for d in DECILES + ("all",):
            mask = np.ones_like(decile, dtype=bool) if d == "all" else decile == d
            w = weight[mask]
            total_weight = float(w.sum())
            base_total = float(np.sum(w * base_income[mask]))
            change_total = float(np.sum(w * change[mask]))
            person_weight = w * people[mask]
            person_total = float(person_weight.sum())
            changed = int(np.count_nonzero((np.abs(change[mask]) > 0.005) & (w > 0)))
            if small(changed):
                rows.append(
                    {
                        "decile": d,
                        "suppressed": True,
                        "mean_change": None,
                        "relative_change": None,
                        "share_gaining": None,
                        "share_losing": None,
                    }
                )
                continue
            rows.append(
                {
                    "decile": d,
                    "suppressed": False,
                    # Whether any household with weight changed: published
                    # only for rows of 10 or more changed households, or none.
                    "any_change": changed > 0,
                    "mean_change": round(change_total / total_weight)
                    if total_weight
                    else float("nan"),
                    "relative_change": round(change_total / base_total, 3)
                    if base_total
                    else float("nan"),
                    "share_gaining": round(
                        float(np.sum(person_weight * (change[mask] > 1)))
                        / person_total,
                        3,
                    )
                    if person_total
                    else float("nan"),
                    "share_losing": round(
                        float(np.sum(person_weight * (change[mask] < -1)))
                        / person_total,
                        3,
                    )
                    if person_total
                    else float("nan"),
                }
            )
        outside = ~np.isin(decile, DECILES) & (weight > 0)
        excluded = float(np.sum(weight[outside]))
        if excluded:
            how_many = (
                f"fewer than {MIN_CELL} households"
                if small(int(outside.sum()))
                else f"{excluded:,.0f} households"
            )
            notes.append(
                f"{fiscal_year_label(year)}: {how_many} with negative income have "
                "no decile and appear only in 'all'"
            )
        impacts[key] = rows
    return impacts, notes


def _runtime_differences(
    base: Mapping, head: Mapping, ignore=("policyengine-uk",)
) -> list:
    """Installed distributions, Python and machine that differ between sides.

    ``ignore`` names the distributions the comparison is about: the model
    (compared separately), and on the data axis the data package too.
    """

    def listing(result):
        return {
            line.split("==")[0]: line
            for line in (result.get("runtime") or {}).get("distributions", [])
        }

    b, h = listing(base), listing(head)
    differences = []
    for name in sorted(set(b) | set(h)):
        if name in ignore:
            continue
        if b.get(name) != h.get(name):
            differences.append(
                f"{b.get(name, f'{name} absent')} -> {h.get(name, f'{name} absent')}"
            )
    for field in ("python", "machine"):
        bv, hv = (
            (base.get("runtime") or {}).get(field),
            (head.get("runtime") or {}).get(field),
        )
        if bv != hv:
            differences.append(f"{field}: {bv} -> {hv}")
    return differences


def compare(
    base: Optional[Mapping],
    head: Optional[Mapping],
    spec: Spec,
    base_households: Optional[Mapping] = None,
    head_households: Optional[Mapping] = None,
    strict: bool = False,
    require_base: bool = True,
    axis: str = "model",
) -> dict:
    """Compare two measurements.

    With ``require_base`` (the default) a missing or crashed base fails the
    comparison: without it there is nothing to show the change against.

    ``axis`` says what may differ between the sides. On the ``model`` axis
    (a change to this model) both must run on the same verified dataset. On
    the ``data`` axis (a change to the data) both must run the same model:
    the same policyengine-uk version and file fingerprint, the same runtime
    with no locally installed dependency, the same partition and metric
    definitions, so every move is the data's. Households are not
    matched across datasets on the data axis; each side's own deciles are
    compared instead.
    """
    if axis not in ("model", "data"):
        raise ValueError(f"axis must be model or data, not {axis!r}")
    failures, warnings = [], []
    if head and head.get("status") == "skipped":
        return {
            "schema": TOOL_SCHEMA + "/comparison",
            "status": "skipped",
            "failures": [],
            "warnings": [f"Not measured: {head.get('reason', 'no reason recorded')}"],
            "years": spec.years,
            "checks": [],
            "rows": [],
            "flags": [],
            "deciles": {},
            "decile_notes": [],
            "decile_flags": [],
            "runtime_differences": [],
            "base": _side_summary(base),
            "head": _side_summary(head),
        }
    head_ok = bool(head) and head.get("status") == "ok"
    base_ok = bool(base) and base.get("status") == "ok"
    if not head:
        failures.append(
            "The head measurement produced no result; see the measure job's log."
        )
    elif not head_ok:
        failures.append(
            "The head measurement crashed: " + _last_line(head.get("error"))
        )
    base_problem = None
    if not base:
        base_problem = "The base measurement produced no result"
    elif not base_ok:
        base_problem = "The base measurement crashed: " + _last_line(base.get("error"))
    if base_problem and require_base:
        failures.append(base_problem + "; the change cannot be compared without it.")
    elif base_problem:
        warnings.append(base_problem + "; the head's own checks decide.")

    years = (head or base or {}).get("years") or spec.years
    if head_ok and base_ok:
        if base.get("years") != head.get("years"):
            failures.append(
                f"Base and head measured different years ({base.get('years')} vs {head.get('years')})."
            )
        b_sha = (base.get("provenance") or {}).get("dataset", {}).get("verified_sha256")
        h_sha = (head.get("provenance") or {}).get("dataset", {}).get("verified_sha256")
        runtime_differences = _runtime_differences(base, head)
        if axis == "model":
            if not b_sha or not h_sha or b_sha != h_sha:
                failures.append(
                    f"Base and head did not run on the same verified dataset ({b_sha} vs {h_sha})."
                )
            if (base.get("partition") or {}).get("sha256") != (
                head.get("partition") or {}
            ).get("sha256"):
                warnings.append(
                    "This change edits the fiscal partition; review the partition diff alongside the moves it explains."
                )
            if runtime_differences:
                warnings.append(
                    "Base and head ran on different runtimes, so some changes may come from dependencies: "
                    + "; ".join(runtime_differences[:10])
                )
        else:
            failures += _same_model_problems(
                base,
                head,
                _runtime_differences(
                    base, head, ignore=("policyengine-uk", "policyengine-uk-data")
                ),
            )
            if not b_sha or not h_sha:
                failures.append(
                    "Each side must record the bytes of the dataset it measured."
                )
            elif b_sha == h_sha:
                warnings.append("Both sides measured the same dataset bytes.")
    else:
        runtime_differences = []

    base_checks, head_checks = _check_map(base), _check_map(head)
    same_partition = (
        base_ok
        and head_ok
        and (base.get("partition") or {}).get("sha256")
        == (head.get("partition") or {}).get("sha256")
    )
    checks = []
    if head_ok:
        missing = [c for c in REQUIRED_CHECKS if c not in head_checks]
        if missing:
            failures.append(
                "The head measurement did not run: " + ", ".join(missing) + "."
            )
    for check_id in dict.fromkeys(list(head_checks) + list(base_checks)):
        b, h = base_checks.get(check_id), head_checks.get(check_id)
        blocking = check_id.startswith(ALWAYS_BLOCKING_PREFIXES) or not base_ok
        classification = classify_check(
            b["status"] if b else None,
            h["status"] if h else None,
            blocking,
            (b or {}).get("failing", {}),
            (h or {}).get("failing", {}),
        )
        if strict and classification == "pre_existing":
            classification = "regression"
        if classification == "skipped" and b and b["status"] != "skipped":
            warnings.append(
                f"The check {check_id} no longer applies on the head: "
                + "; ".join((h or {}).get("details", [])[:1])
            )
        if classification == "removed" and head_ok:
            # A check can disappear with the head it checked; otherwise its
            # disappearance would let a failure pass unseen.
            if same_partition:
                failures.append(
                    f"The check {check_id} ran on the base but not on the head."
                )
            else:
                warnings.append(
                    f"The check {check_id} ran on the base but not on the head "
                    "(the partition changed)."
                )
        template = h or b
        checks.append(
            {
                "id": check_id,
                "label": template["label"],
                "section": template.get("section", ""),
                "base_status": b["status"] if b else None,
                "head_status": h["status"] if h else None,
                "classification": classification,
                "head_details": (h or {}).get("details", []),
                "base_details": (b or {}).get("details", []),
            }
        )
    regressions = [c for c in checks if c["classification"] == "regression"]
    for check in regressions:
        failures.append(
            f"{check['label']} ({check['id']}): " + "; ".join(check["head_details"][:3])
        )

    rows, flags = compare_metrics(
        _metric_map(base),
        _metric_map(head),
        spec,
        years,
        base_hidden=(base_households or {}).get(HIDDEN_KEY),
        head_hidden=(head_households or {}).get(HIDDEN_KEY),
    )
    if any(
        m.get("rounded")
        for m in (head or {}).get("metrics", []) + (base or {}).get("metrics", [])
    ):
        warnings.append(
            "Totals that contain a figure from fewer than 10 records are rounded to the "
            "nearest £1bn, and decile mean incomes to £1,000, in the years it is "
            "suppressed, so it cannot be recovered from them. Their changes are exact "
            "where no suppressed figure inside them changed, and withheld otherwise."
        )
    non_finite = []
    for row in rows:
        if row["only_in"] == "base" and head_ok:
            warnings.append(
                f"{row['label']} ({row['id']}) is measured on the base only."
            )
        elif row["only_in"] == "head" and base_ok:
            warnings.append(
                f"{row['label']} ({row['id']}) is measured on the head only."
            )
        if row["only_in"] != "base":
            non_finite += [
                f"{row['id']} {fiscal_year_label(int(year))}"
                for year, cell in row["values"].items()
                if not _finite(cell["head"]) and not cell["head_suppressed"]
            ]
    if non_finite and head_ok:
        more = f" and {len(non_finite) - 10} more" if len(non_finite) > 10 else ""
        failures.append(
            "The head has figures that are missing or not finite: "
            + "; ".join(non_finite[:10])
            + more
            + "."
        )

    deciles, decile_notes, decile_flags = {}, [], []
    if axis == "data":
        decile_notes.append(
            "The datasets hold different households, so households are not "
            "matched; compare the mean income in each side's own deciles."
        )
    elif head_ok and base_ok and base_households and head_households:
        deciles, decile_notes = decile_impacts(base_households, head_households, years)
        threshold = spec.threshold("decile_relative")
        for year, decile_rows in deciles.items():
            for row in decile_rows:
                rel = row["relative_change"]
                if (
                    threshold is not None
                    and rel is not None
                    and _finite(rel)
                    and abs(rel) > threshold.limit(0)
                ):
                    decile_flags.append({"year": int(year), **row})

    return {
        "schema": TOOL_SCHEMA + "/comparison",
        "axis": axis,
        "status": "fail" if failures else "pass",
        "failures": failures,
        "warnings": warnings,
        "years": years,
        "checks": checks,
        "rows": rows,
        "flags": flags,
        "deciles": deciles,
        "decile_notes": decile_notes,
        "decile_flags": decile_flags,
        "runtime_differences": runtime_differences,
        "base": _side_summary(base),
        "head": _side_summary(head),
    }


def _same_model_problems(base: Mapping, head: Mapping, runtime_differences) -> list:
    """What stops a data comparison from attributing its moves to the data.

    Each side must record the model it imported (version and a fingerprint
    of its files), its runtime, partition and metric definitions, and they
    must agree. A missing field is a failure: one model cannot be shown.
    The caller's own commit (``git_sha``) identifies the measuring checkout,
    not the model, so it is not part of the identity.
    """
    problems = []

    def field(result, *path):
        value = result
        for key in path:
            value = (value or {}).get(key)
        return value

    identity = {
        "policyengine-uk version": ("runtime", "policyengine_uk"),
        "policyengine-uk fingerprint": ("runtime", "policyengine_uk_fingerprint"),
        "runtime listing": ("runtime", "distributions"),
        "fiscal partition": ("partition", "sha256"),
        "metric definitions": ("provenance", "metrics_version"),
    }
    for name, path in identity.items():
        b, h = field(base, *path), field(head, *path)
        if not b or not h:
            problems.append(
                f"A data comparison needs the {name} of both sides, and "
                f"{'the base' if not b else 'the head'} does not record it."
            )
        elif name != "runtime listing" and b != h:
            shown = (
                f"{str(b)[:12]} and {str(h)[:12]}"
                if name.endswith(("fingerprint", "partition"))
                else f"{b} and {h}"
            )
            problems.append(
                f"A data comparison needs one {name}, but the sides have {shown}."
            )
    if runtime_differences:
        problems.append(
            "A data comparison needs one runtime, but base and head differ in: "
            + "; ".join(runtime_differences[:10])
        )
    # A dependency installed from a local directory can differ from the
    # version it reports; the model and the data package are identified
    # otherwise (Sol review of #2425).
    exempt = {"policyengine-uk", "policyengine-uk-data"}
    for side, result in (("base", base), ("head", head)):
        local = field(result, "runtime", "local_installs")
        if local is None:
            problems.append(
                f"A data comparison needs the local installs of both sides, and "
                f"the {side} does not record them."
            )
        elif set(local) - exempt:
            problems.append(
                f"A data comparison needs released dependencies, but the {side} "
                "has local or editable installs of "
                + ", ".join(sorted(set(local) - exempt))
                + ", whose version doesn't identify their files."
            )
    return problems


def _last_line(text) -> str:
    lines = [line for line in str(text or "").strip().splitlines() if line.strip()]
    return lines[-1] if lines else "no error recorded"


def _side_summary(result: Optional[Mapping]) -> Optional[dict]:
    if not result:
        return None
    return {
        "status": result.get("status"),
        "label": result.get("label"),
        "provenance": result.get("provenance"),
        "runtime": {
            k: v
            for k, v in (result.get("runtime") or {}).items()
            if k != "distributions"
        },
        "partition": {
            k: (result.get("partition") or {}).get(k) for k in ("source", "sha256")
        },
        "guard": result.get("guard"),
        "reforms": result.get("reforms"),
        "timings": result.get("timings"),
        "error": result.get("error"),
    }
