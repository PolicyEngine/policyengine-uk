"""Compare a base and a head measurement.

The comparison fails when the head did not run, ran on different data, or
broke a check the base passes; it reports, without failing, checks both sides
fail (pre-existing) and moves above the flag thresholds.
"""

from __future__ import annotations

import math
from typing import Mapping, Optional

import numpy as np

from . import TOOL_SCHEMA
from .spec import Spec, fiscal_year_label

# Failing these on the head blocks the change whatever the base did: a
# non-finite or crashed result cannot be compared at all.
ALWAYS_BLOCKING_PREFIXES = ("finite:", "weights:")

FLAG_KIND_BY_SECTION = {
    "reforms": "reform_gbp",
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
    base_status: Optional[str], head_status: Optional[str], blocking: bool
) -> str:
    """How a check's outcome on the head relates to the base.

    Returns one of: ``pass``, ``regression``, ``pre_existing``, ``fixed``,
    ``new_warning``, ``warning``, ``removed``.
    """
    if head_status is None:
        return "removed"
    if head_status == "pass":
        return "fixed" if base_status in ("fail", "warn") else "pass"
    if head_status == "warn":
        return "warning" if base_status == "warn" else "new_warning"
    # head failed
    if blocking or base_status in (None, "pass"):
        return "regression"
    if base_status == "warn":
        return "regression"
    return "pre_existing"


def compare_metrics(base: Mapping, head: Mapping, spec: Spec, years) -> tuple:
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
            "changed": False,
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
            delta = h - b if _finite(b) and _finite(h) else None
            row["values"][key] = {"base": b, "head": h, "delta": delta}
            if delta is not None and delta != 0:
                row["changed"] = True
            if delta is not None and threshold is not None and threshold.exceeded(b, h):
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
    """Indices into head arrays that line up with base households, or None."""
    if base_ids.shape == head_ids.shape and np.array_equal(base_ids, head_ids):
        return np.arange(len(head_ids))
    order = np.argsort(head_ids, kind="stable")
    positions = np.searchsorted(head_ids[order], base_ids)
    positions = np.clip(positions, 0, len(order) - 1)
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
            rows.append(
                {
                    "decile": d,
                    "households": total_weight,
                    "base_mean": base_total / total_weight
                    if total_weight
                    else float("nan"),
                    "mean_change": change_total / total_weight
                    if total_weight
                    else float("nan"),
                    "relative_change": change_total / base_total
                    if base_total
                    else float("nan"),
                    "share_gaining": float(np.sum(person_weight * (change[mask] > 1)))
                    / person_total
                    if person_total
                    else float("nan"),
                    "share_losing": float(np.sum(person_weight * (change[mask] < -1)))
                    / person_total
                    if person_total
                    else float("nan"),
                }
            )
        excluded = float(np.sum(weight[~np.isin(decile, DECILES)]))
        if excluded:
            notes.append(
                f"{fiscal_year_label(year)}: {excluded:,.0f} households with negative "
                "income have no decile and appear only in 'all'"
            )
        impacts[key] = rows
    return impacts, notes


def _runtime_differences(base: Mapping, head: Mapping) -> list:
    def listing(result):
        return {
            line.split("==")[0]: line
            for line in (result.get("runtime") or {}).get("distributions", [])
        }

    b, h = listing(base), listing(head)
    differences = []
    for name in sorted(set(b) | set(h)):
        if name == "policyengine-uk":
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
) -> dict:
    failures, warnings = [], []
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
    if not base:
        warnings.append(
            "The base measurement produced no result, so nothing is compared against it."
        )
    elif not base_ok:
        warnings.append(
            "The base measurement crashed, so the head's own checks decide: "
            + _last_line(base.get("error"))
        )

    years = (head or base or {}).get("years") or spec.years
    if head_ok and base_ok:
        if base.get("years") != head.get("years"):
            failures.append(
                f"Base and head measured different years ({base.get('years')} vs {head.get('years')})."
            )
        b_sha = (base.get("provenance") or {}).get("dataset", {}).get("verified_sha256")
        h_sha = (head.get("provenance") or {}).get("dataset", {}).get("verified_sha256")
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
        runtime_differences = _runtime_differences(base, head)
        if runtime_differences:
            warnings.append(
                "Base and head ran on different runtimes, so some changes may come from dependencies: "
                + "; ".join(runtime_differences[:10])
            )
    else:
        runtime_differences = []

    base_checks, head_checks = _check_map(base), _check_map(head)
    checks = []
    for check_id in dict.fromkeys(list(head_checks) + list(base_checks)):
        b, h = base_checks.get(check_id), head_checks.get(check_id)
        blocking = check_id.startswith(ALWAYS_BLOCKING_PREFIXES) or not base_ok
        classification = classify_check(
            b["status"] if b else None, h["status"] if h else None, blocking
        )
        if strict and classification == "pre_existing":
            classification = "regression"
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

    rows, flags = compare_metrics(_metric_map(base), _metric_map(head), spec, years)
    for row in rows:
        if row["only_in"] == "base" and head_ok:
            warnings.append(
                f"{row['label']} ({row['id']}) is measured on the base only."
            )

    deciles, decile_notes, decile_flags = {}, [], []
    if head_ok and base_ok and base_households and head_households:
        deciles, decile_notes = decile_impacts(base_households, head_households, years)
        threshold = spec.threshold("decile_relative")
        for year, decile_rows in deciles.items():
            for row in decile_rows:
                rel = row["relative_change"]
                if (
                    threshold is not None
                    and _finite(rel)
                    and abs(rel) > threshold.limit(0)
                ):
                    decile_flags.append({"year": int(year), **row})

    return {
        "schema": TOOL_SCHEMA + "/comparison",
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
