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
from .privacy import MIN_CELL, small
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


def _excludes(metric: Optional[Mapping], key: str) -> dict:
    """The suppressed components a total leaves out in ``key``, with their
    signs."""
    return dict(((metric or {}).get("excludes") or {}).get(key) or {})


def _additive(metric_id: str, section: str) -> bool:
    """Whether a metric is a plain sum of heads in pounds, so heads can be
    taken out of it by subtraction. Decile means (per household) and the HBAI
    total (reset at zero) are not (Sol re-review 6 of #2335)."""
    return section in ("model_totals", "balance") or metric_id == (
        "household.household_net_income"
    )


def _aligned(value, metric_excludes: Mapping, union: Mapping, metrics: Mapping, key):
    """``value`` with every head in ``union`` taken out, using published heads.

    A head excluded on the other side only is published on this side, so it
    can be taken out here from its published value: the two sides then leave
    out the same heads, and their difference is the published heads' change.
    """
    for head_id, sign in union.items():
        if head_id in metric_excludes:
            continue
        published = _published(metrics, head_id, key)
        if not _finite(published):
            return None
        value = value - sign * published
    return value


def _published(metrics: Mapping, metric_id: str, key: str):
    metric = metrics.get(metric_id)
    return None if metric is None else metric["values"].get(key)


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
            # containing one is rebuilt without it (privacy.py,
            # measure.rebuild_protected).
            b_hidden = key in (base_metric or {}).get("suppressed", ())
            h_hidden = key in (head_metric or {}).get("suppressed", ())
            b_ex, h_ex = _excludes(base_metric, key), _excludes(head_metric, key)
            union = {**b_ex, **h_ex}
            if b_hidden or h_hidden:
                # A head from fewer than 10 records: its change is too.
                delta = None
            elif not (_finite(b) and _finite(h)):
                delta = None
            elif b_ex == h_ex:
                delta = h - b
            elif not _additive(metric_id, template["section"]):
                # Different exclusions can't be lined up in a mean or a
                # clipped total.
                delta = None
            else:
                # The sides leave out different components: take the union
                # out of both, from published values only.
                b_al = _aligned(b, b_ex, union, base, key)
                h_al = _aligned(h, h_ex, union, head, key)
                delta = None if b_al is None or h_al is None else h_al - b_al
            row["values"][key] = {
                "base": b,
                "head": h,
                "delta": delta,
                "base_suppressed": b_hidden,
                "head_suppressed": h_hidden,
                # The suppressed components this total leaves out, on either
                # side.
                "excludes": sorted(union),
                # No change can be shown: a side is suppressed, or the sides
                # leave out different components and can't be lined up. Not
                # "no change" (Sol re-review 7 of #2335).
                "withheld": delta is None
                and bool(base_metric and head_metric)
                and (b_hidden or h_hidden or (_finite(b) and _finite(h))),
            }
            if (delta is not None and delta != 0) or row["values"][key]["withheld"]:
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


def decile_impacts(
    base_households: Mapping, head_households: Mapping, years, withheld=()
) -> tuple:
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
    - The income each side records leaves out any component suppressed that
      year (``measure.rebuild_protected``), so no row carries a figure from
      fewer than ``MIN_CELL`` records; a year whose sides leave out different
      ones is withheld, with a note.
    - No row publishes its households' weight or base income, and changes
      are given to the precision the comment shows (£1 and 0.1%).
    """
    impacts, notes = {}, []
    for year in years:
        key = str(year)
        b, h = base_households.get(key), head_households.get(key)
        if key in {str(y) for y in withheld}:
            notes.append(
                f"{fiscal_year_label(year)}: decile changes are withheld: households "
                f"are ranked on an income holding a figure from fewer than {MIN_CELL} "
                "records"
            )
            continue
        if b is None or h is None:
            notes.append(f"{fiscal_year_label(year)}: household detail missing")
            continue
        matched = _match(np.asarray(b["household_id"]), np.asarray(h["household_id"]))
        if matched is None:
            notes.append(f"{fiscal_year_label(year)}: base and head households differ")
            continue
        b_ex = sorted(str(x) for x in np.asarray(b.get("excludes", [])).ravel())
        h_ex = sorted(str(x) for x in np.asarray(h.get("excludes", [])).ravel())
        if b_ex != h_ex:
            # Each side's income leaves out its own suppressed components;
            # with different sets, a household's change would mix
            # definitions (Sol re-review 6 of #2335).
            notes.append(
                f"{fiscal_year_label(year)}: a figure from fewer than {MIN_CELL} "
                "records is suppressed on one side only, so decile changes are "
                "withheld"
            )
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
    require_base: bool = True,
) -> dict:
    """Compare two measurements.

    With ``require_base`` (the default) a missing or crashed base fails the
    comparison: without it there is nothing to show the change against.
    """
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

    rows, flags = compare_metrics(_metric_map(base), _metric_map(head), spec, years)
    excluded = sorted(
        {
            head_id
            for m in (head or {}).get("metrics", []) + (base or {}).get("metrics", [])
            for heads in (m.get("excludes") or {}).values()
            for head_id in heads
        }
    )
    if excluded:
        warnings.append(
            "In the years a figure from fewer than 10 records is suppressed ("
            + ", ".join(excluded)
            + "), every total containing it, and the decile incomes, are rebuilt "
            "from their other components, so no published total includes it. "
            "Those totals are marked †. A change is withheld where the two sides "
            "leave out different figures and can't be lined up."
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
    # Years a side ranks households on an income holding a suppressed figure:
    # it publishes no decile figure and keeps no household detail
    # (measure.measure_year).
    withheld = [
        year
        for year in years
        for side in (base, head)
        if str(year)
        in (_metric_map(side).get("deciles.mean_income.1") or {}).get("suppressed", ())
    ]
    if head_ok and base_ok and ((base_households and head_households) or withheld):
        # With every year withheld there is no household detail at all, and
        # the notes say why (Sol re-review 8 of #2335).
        deciles, decile_notes = decile_impacts(
            base_households or {}, head_households or {}, years, withheld
        )
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
