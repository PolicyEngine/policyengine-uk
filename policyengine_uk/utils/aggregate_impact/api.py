"""In-process entry point for qualification (policyengine.py, workstream W4).

``compute_budget_metrics`` measures one simulation and returns a long-format
report: one row per metric and year, plus the identity and partition checks.
Two pairs are comparable when their reports share ``metrics_version`` (the
same tool code, and the same effective spec, horizon and reforms), whatever
model each pair runs; each model's own
fiscal partition is read from the measured package, and its digest is
``partition_version``.

To hold the definitions fixed across models, copy this package directory
from one policyengine-uk commit and import the copy under another name: it
imports only its own modules and policyengine_uk's public simulation API.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Callable, Optional, Sequence

from . import TOOL_SCHEMA
from .measure import measure
from .partition import Partition, default_partition_path, load_partition
from .reforms import load_reforms
from .spec import DEFAULT_SPEC_PATH, Spec, load_spec

KIND_BY_SECTION = {
    "receipts": "receipt",
    "spending": "spending",
    "caseloads": "caseload",
    "poverty": "poverty",
    "poverty_count": "poverty_count",
    "inequality": "inequality",
    "deciles": "decile",
    "balance": "balance",
    "model_totals": "model_total",
    "double_counts": "double_count",
    "household_totals": "household_total",
    "population": "population",
    "reforms": "reform",
    "reform_targets": "reform_target",
}
PARTITIONED_SECTIONS = {"receipts", "spending", "caseloads"}


def _spec_for_years(spec: Spec, years: Optional[Sequence[int]]) -> Spec:
    if not years:
        return spec
    years = sorted(int(y) for y in years)
    guard_year = spec.guard_year if spec.guard_year in years else years[0]
    return dataclasses.replace(
        spec, first_year=years[0], last_year=years[-1], guard_year=guard_year
    )


def to_report(result: dict) -> dict:
    """Flatten a measurement into the long-format qualification report."""
    provenance = result.get("provenance") or {}
    report = {
        "schema": TOOL_SCHEMA + "/report",
        "status": result.get("status"),
        "metrics_version": provenance.get("metrics_version"),
        "partition_version": (result.get("partition") or {}).get("sha256"),
        "years": result.get("years"),
        "metrics": [],
        "identities": [],
    }
    if result.get("status") != "ok":
        report["error"] = result.get("error")
        return report
    for metric in result["metrics"]:
        section = metric["section"]
        head_id = (
            metric["id"].split(".", 1)[1] if section in PARTITIONED_SECTIONS else None
        )
        for year, value in metric["values"].items():
            report["metrics"].append(
                {
                    "metric_id": metric["id"],
                    "year": int(year),
                    # None when the figure comes from fewer than 10 records.
                    "value": value,
                    "suppressed": year in metric.get("suppressed", ()),
                    # The suppressed components this total is rebuilt without
                    # that year (measure.rebuild_protected); compare totals at
                    # equal exclusion.
                    "excludes": sorted((metric.get("excludes") or {}).get(year) or {}),
                    # The sign each enters the total with (+1 or -1), so two
                    # additive totals with different exclusions can be lined
                    # up from published figures (compare._aligned).
                    "exclude_signs": dict(
                        sorted(((metric.get("excludes") or {}).get(year) or {}).items())
                    ),
                    "unit": metric["kind"],
                    "kind": KIND_BY_SECTION.get(section, section),
                    "partition": head_id,
                    "label": metric["label"],
                }
            )
    for check in result["checks"]:
        report["identities"].append(
            {
                "identity_id": check["id"],
                "year": None,
                "status": check["status"],
                "severity": check["severity"],
                # The years the check failed in ("" for a check with no year),
                # so a consumer can tell a newly failing year from an old one.
                "failing_scopes": sorted(check.get("failing") or {}),
                "detail": "; ".join(check["details"]),
            }
        )
    return report


def compute_budget_metrics(
    sim,
    factory: Optional[Callable] = None,
    *,
    years: Optional[Sequence[int]] = None,
    partition: Optional[Partition] = None,
    spec: Optional[Spec] = None,
    reforms: Optional[Sequence] = None,
    run_guard: bool = True,
    label: str = "candidate",
    provenance: Optional[dict] = None,
) -> dict:
    """Measure ``sim`` (a fresh ``Microsimulation``) and return the report.

    ``factory(reform=None)`` builds another simulation on the same data; by
    default it rebuilds ``type(sim)`` from ``sim.dataset``. ``reforms``
    defaults to the standard set (``standard_reforms.yaml``), each costed and
    checked for responsiveness; pass ``[]`` to cost none. A failed identity
    has status ``fail``; ``warn`` rows (a head that is zero everywhere) are
    observations, not failures.
    """
    spec = _spec_for_years(spec or load_spec(DEFAULT_SPEC_PATH), years)
    if partition is None:
        path = default_partition_path()
        if path is None:
            raise FileNotFoundError(
                "the measured policyengine_uk ships no fiscal partition"
            )
        partition = load_partition(path)
    if factory is None:
        dataset = sim.dataset
        simulation_class = type(sim)

        def factory(reform=None):
            return simulation_class(dataset=dataset, reform=reform or None)

    if reforms is None:
        reforms = load_reforms()
    provenance = dict(provenance or {})
    result, _ = measure(
        sim,
        factory,
        partition,
        spec,
        label=label,
        reforms=reforms,
        run_guard=run_guard,
        provenance=provenance,
    )
    return to_report(result)
