"""Measure one model checkout on one dataset over the report horizon."""

from __future__ import annotations

import gc
import hashlib
import json
import platform
import re
import sys
import time
from importlib import metadata
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

import numpy as np

from . import TOOL_SCHEMA
from .guard import counted_once, snapshot_inputs
from .partition import Partition, closure_problems, group_label, read_model_lists
from .reforms import StandardReform, parse_reforms, reform_parameters, responsiveness
from .spec import Spec, fiscal_year_label

ENTITIES = ("person", "benunit", "household")

# Model totals reported alongside the partition. Each is a household variable.
HOUSEHOLD_TOTALS = {
    "household_market_income": "Household market income",
    "household_net_income": "Household net income",
    "hbai_household_net_income": "Household net income (HBAI definition)",
}


class Recorder:
    """Collects metric values and check outcomes for one measurement."""

    def __init__(self):
        self.metrics: dict = {}
        self.checks: dict = {}

    def metric(
        self, metric_id, label, section, kind, year, value, group=None, unit=None
    ):
        record = self.metrics.setdefault(
            metric_id,
            {
                "id": metric_id,
                "label": label,
                "section": section,
                "group": group,
                "kind": kind,
                "unit": unit,
                "values": {},
            },
        )
        record["values"][str(year)] = float(value)

    def check(self, check_id, label, ok, detail="", severity="fail", section=""):
        """Record a check; repeated ids (one per year) merge into one result."""
        status = "pass" if ok else ("warn" if severity == "warn" else "fail")
        record = self.checks.get(check_id)
        if record is None:
            record = {
                "id": check_id,
                "label": label,
                "section": section,
                "severity": severity,
                "status": status,
                "details": [],
            }
            self.checks[check_id] = record
        elif status != "pass" and record["status"] == "pass":
            record["status"] = status
        if not ok and detail:
            record["details"].append(detail)


def array(sim, variable: str, period, map_to: Optional[str] = None) -> np.ndarray:
    """A variable's raw values, without survey weights."""
    try:
        result = sim.calculate(variable, period, map_to=map_to, unweighted=True)
    except TypeError:
        result = sim.calculate(variable, period, map_to=map_to)
    return np.asarray(getattr(result, "values", result))


def active_parameters(sim, partition: Partition, year) -> set:
    """The ``dropped_when`` switches that are on in ``year``."""
    active = set()
    for path in partition.dropped_when_parameters():
        node = sim.tax_benefit_system.parameters
        try:
            for part in path.split("."):
                node = getattr(node, part)
            if bool(node(f"{year}-01-01")):
                active.add(path)
        except AttributeError:
            continue
    return active


def entity_of(sim, variable: str) -> str:
    return sim.tax_benefit_system.variables[variable].entity.key


def to_household(sim, values: np.ndarray, entity: str) -> np.ndarray:
    if entity == "household":
        return np.asarray(values, dtype=np.float64)
    return np.asarray(
        sim.map_result(np.asarray(values, dtype=np.float64), entity, "household"),
        dtype=np.float64,
    )


def weighted_gini(values: np.ndarray, weights: np.ndarray) -> float:
    """Gini coefficient of ``values`` with non-negative ``weights``."""
    values = np.asarray(values, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    keep = weights > 0
    values, weights = values[keep], weights[keep]
    if values.size == 0:
        return float("nan")
    order = np.argsort(values, kind="stable")
    values, weights = values[order], weights[order]
    cumulative_weight = np.cumsum(weights)
    cumulative_income = np.cumsum(weights * values)
    total_weight, total_income = cumulative_weight[-1], cumulative_income[-1]
    if total_income == 0:
        return float("nan")
    previous = np.concatenate([[0.0], cumulative_income[:-1]])
    area = np.sum(weights * (cumulative_income + previous)) / (
        total_weight * total_income
    )
    return float(1.0 - area)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def tool_digest() -> str:
    """SHA-256 of this package's code and spec, independent of where it lives."""
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.suffix in (".py", ".yaml") and "__pycache__" not in path.parts:
            digest.update(path.relative_to(root).as_posix().encode() + b"\0")
            digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def runtime_identity() -> dict:
    """The installed distributions and interpreter that ran the measurement."""
    distributions = sorted(
        {
            (d.metadata["Name"].lower().replace("_", "-"), d.version)
            for d in metadata.distributions()
            if d.metadata["Name"]
        }
    )
    listing = "\n".join(f"{name}=={version}" for name, version in distributions)

    def version(name):
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            return None

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "policyengine_uk": version("policyengine-uk"),
        "policyengine_core": version("policyengine-core"),
        "numpy": version("numpy"),
        "distributions": [f"{n}=={v}" for n, v in distributions],
        "distributions_sha256": hashlib.sha256(listing.encode()).hexdigest(),
    }


def _identity_check(rec, check_id, label, components_hh, total_hh, year, spec):
    """Household-level accounting identity: components add up to the total."""
    difference = components_hh - total_hh
    scale = np.abs(total_hh) + 1.0
    tolerance = 1.0 + spec.identity_relative_tolerance * scale
    bad = np.abs(difference) > tolerance
    finite = np.all(np.isfinite(difference))
    ok = bool(finite and not bad.any())
    detail = ""
    if not ok:
        worst = int(np.nanargmax(np.abs(difference))) if difference.size else 0
        detail = (
            f"{fiscal_year_label(year)}: {int(bad.sum())} households differ; "
            f"largest gap £{float(difference[worst]):,.2f}"
        )
    rec.check(check_id, label, ok, detail, section="identities")


def measure_year(
    sim, partition: Partition, spec: Spec, year: int, rec: Recorder, households: dict
):
    tbs_variables = sim.tax_benefit_system.variables
    weights = {e: array(sim, f"{e}_weight", year).astype(np.float64) for e in ENTITIES}
    for entity, label in (
        ("person", "People"),
        ("benunit", "Benefit units"),
        ("household", "Households"),
    ):
        w = weights[entity]
        rec.check(
            f"weights:{entity}",
            f"{label} weights are finite and non-negative",
            bool(np.all(np.isfinite(w)) and np.all(w >= 0)),
            f"{fiscal_year_label(year)}: invalid {entity} weights",
            section="data",
        )
        rec.metric(f"population.{entity}", label, "population", "count", year, w.sum())
    hw = weights["household"]

    head_hh = {}
    for head in partition.heads:
        entity = entity_of(sim, head.variable)
        values = array(sim, head.variable, year).astype(np.float64)
        finite = np.isfinite(values)
        rec.check(
            f"finite:{head.id}",
            f"{head.label} is finite for every unit",
            bool(finite.all()),
            f"{fiscal_year_label(year)}: {int((~finite).sum())} non-finite values",
            section="finite",
        )
        hh = to_household(sim, values, entity)
        head_hh[head.variable] = hh
        section = "receipts" if head.kind == "tax" else "spending"
        rec.metric(
            f"{section}.{head.id}",
            head.label,
            section,
            "gbp",
            year,
            float(np.sum(hw * hh)),
            group=group_label(head.report_group),
        )
        if head.kind == "spending" and head.caseload:
            rec.metric(
                f"caseloads.{head.id}",
                head.label,
                "caseloads",
                "count",
                year,
                float(np.sum(weights[entity] * (values > 0))),
                group=group_label(head.report_group),
                unit=entity,
            )
        if head.sign == "nonnegative":
            negative = values < -0.005
            rec.check(
                f"sign:{head.id}",
                f"{head.label} is never negative",
                not bool(negative.any()),
                f"{fiscal_year_label(year)}: {int(negative.sum())} units below zero, "
                f"minimum £{float(np.nanmin(values)):,.2f}",
                section="signs",
            )
        if not head.zero_at_baseline:
            rec.check(
                f"inert:{head.id}",
                f"{head.label} is not zero for every unit",
                bool(np.any(values != 0)),
                f"{fiscal_year_label(year)}: zero for every unit",
                severity="warn",
                section="coverage",
            )

    double_count_hh = {}
    for dc in partition.double_counts:
        values = array(sim, dc.variable, year).astype(np.float64)
        hh = to_household(sim, values, entity_of(sim, dc.variable))
        double_count_hh[dc.variable] = hh
        rec.metric(
            f"double_counts.{dc.variable}",
            f"{dc.variable}, counted again inside {dc.contained_in}",
            "double_counts",
            "gbp",
            year,
            float(np.sum(hw * hh)),
        )

    active = active_parameters(sim, partition, year)
    model_hh = {}
    for total in partition.totals:
        if total not in tbs_variables:
            continue
        hh = to_household(
            sim, array(sim, total, year).astype(np.float64), entity_of(sim, total)
        )
        model_hh[total] = hh
        rec.metric(
            f"model.{total}", total, "model_totals", "gbp", year, float(np.sum(hw * hh))
        )
        components = np.zeros_like(hh)
        for head in partition.heads_in(total, active):
            components = components + head_hh[head.variable]
        for dc in partition.double_counts_in(total, active):
            components = components + double_count_hh[dc.variable]
        _identity_check(
            rec,
            f"identity:{total}",
            f"The partition's heads and declared double counts add up to {total}",
            components,
            hh,
            year,
            spec,
        )

    def partition_sum(total):
        out = np.zeros_like(hw)
        for head in partition.heads_in(total, active):
            out = out + head_hh[head.variable]
        return out

    receipts = partition_sum("gov_tax")
    spending = partition_sum("gov_spending")
    rec.metric(
        "balance.receipts",
        "Government receipts, each component once",
        "balance",
        "gbp",
        year,
        float(np.sum(hw * receipts)),
    )
    rec.metric(
        "balance.spending",
        "Government spending",
        "balance",
        "gbp",
        year,
        float(np.sum(hw * spending)),
    )
    rec.metric(
        "balance.balance",
        "Government balance, each receipt once",
        "balance",
        "gbp",
        year,
        float(np.sum(hw * (receipts - spending))),
    )
    household_only = np.zeros_like(hw)
    for head in partition.spending_heads:
        if "household_benefits" in head.totals and "gov_spending" not in head.totals:
            household_only = household_only + head_hh[head.variable]
    rec.metric(
        "balance.household_only_benefits",
        "Benefits in household_benefits but not in gov_spending",
        "balance",
        "gbp",
        year,
        float(np.sum(hw * household_only)),
    )

    if {"gov_balance", "gov_tax", "gov_spending"} <= set(tbs_variables):
        gov_balance = array(sim, "gov_balance", year).astype(np.float64)
        rec.metric(
            "model.gov_balance",
            "gov_balance",
            "model_totals",
            "gbp",
            year,
            float(np.sum(hw * gov_balance)),
        )
        _identity_check(
            rec,
            "identity:gov_balance",
            "gov_balance equals gov_tax minus gov_spending",
            model_hh.get("gov_tax", array(sim, "gov_tax", year))
            - model_hh.get("gov_spending", array(sim, "gov_spending", year)),
            gov_balance,
            year,
            spec,
        )
    for variable, label in HOUSEHOLD_TOTALS.items():
        if variable in tbs_variables:
            values = array(sim, variable, year).astype(np.float64)
            rec.metric(
                f"household.{variable}",
                label,
                "household_totals",
                "gbp",
                year,
                float(np.sum(hw * values)),
            )
    if {
        "household_net_income",
        "household_market_income",
        "household_benefits",
        "household_tax",
        "pension_contributions",
    } <= set(tbs_variables):
        pension = to_household(
            sim,
            array(sim, "pension_contributions", year).astype(np.float64),
            entity_of(sim, "pension_contributions"),
        )
        components = (
            array(sim, "household_market_income", year).astype(np.float64)
            + model_hh.get("household_benefits", array(sim, "household_benefits", year))
            - model_hh.get("household_tax", array(sim, "household_tax", year))
            - pension
        )
        _identity_check(
            rec,
            "identity:household_net_income",
            "Household net income equals market income plus benefits less taxes and pension contributions",
            components,
            array(sim, "household_net_income", year).astype(np.float64),
            year,
            spec,
        )

    pw = weights["person"]
    for measure_spec in spec.poverty_measures:
        try:
            in_poverty = array(
                sim, measure_spec["variable"], year, map_to="person"
            ).astype(bool)
        except Exception as error:  # noqa: BLE001 - recorded, not raised
            rec.check(
                f"available:{measure_spec['id']}",
                f"{measure_spec['label']} can be computed",
                False,
                f"{fiscal_year_label(year)}: {type(error).__name__}: {error}",
                section="coverage",
            )
            continue
        for group in spec.poverty_groups:
            if group.get("variable"):
                try:
                    members = array(sim, group["variable"], year).astype(bool)
                except Exception as error:  # noqa: BLE001
                    rec.check(
                        f"available:{group['id']}",
                        f"{group['label']} can be identified",
                        False,
                        f"{fiscal_year_label(year)}: {type(error).__name__}: {error}",
                        section="coverage",
                    )
                    continue
            else:
                members = np.ones_like(in_poverty, dtype=bool)
            population = float(np.sum(pw * members))
            poor = float(np.sum(pw * (members & in_poverty)))
            rate = poor / population if population > 0 else float("nan")
            rec.check(
                "bounds:poverty_rates",
                "Poverty rates lie between 0 and 1",
                bool(0.0 <= rate <= 1.0),
                f"{fiscal_year_label(year)}: {measure_spec['id']} {group['id']} is {rate}",
                section="bounds",
            )
            metric_id = f"{measure_spec['id']}.{group['id']}"
            label = f"{measure_spec['label']}: {group['label'].lower()}"
            rec.metric(
                f"poverty.{metric_id}",
                label,
                "poverty",
                "rate",
                year,
                rate,
                group=measure_spec["label"],
            )
            rec.metric(
                f"poverty_count.{metric_id}",
                label,
                "poverty_count",
                "count",
                year,
                poor,
                group=measure_spec["label"],
            )

    people = array(sim, "household_count_people", year).astype(np.float64)
    for inequality in spec.inequality:
        income = array(sim, inequality["variable"], year).astype(np.float64)
        rec.metric(
            f"inequality.{inequality['id']}",
            inequality["label"],
            "inequality",
            "index",
            year,
            weighted_gini(income, hw * people),
        )

    decile = array(sim, spec.decile_variable, year).astype(np.int64)
    income = array(sim, spec.income_variable, year).astype(np.float64)
    for d in range(1, 11):
        in_decile = decile == d
        weight = float(np.sum(hw[in_decile]))
        rec.metric(
            f"deciles.mean_income.{d}",
            f"Decile {d}: mean {spec.income_variable} per household",
            "deciles",
            "gbp_household",
            year,
            float(np.sum(hw[in_decile] * income[in_decile])) / weight
            if weight
            else float("nan"),
            group="Own-decile levels",
        )
    households[str(year)] = {
        "household_id": array(sim, "household_id", year).astype(np.int64),
        "household_weight": hw.astype(np.float64),
        "household_count_people": people.astype(np.float64),
        "decile": decile,
        "income": income,
    }


def _finite_metrics_check(rec: Recorder):
    bad = [
        f"{m['id']} {fiscal_year_label(int(year))}"
        for m in rec.metrics.values()
        for year, value in m["values"].items()
        if not np.isfinite(value)
    ]
    rec.check(
        "finite:metrics",
        "Every reported figure is finite",
        not bad,
        "; ".join(bad[:20]) + (f" and {len(bad) - 20} more" if len(bad) > 20 else ""),
        section="finite",
    )


def weighted_total(sim, variable: str, year: int) -> float:
    """The household-weighted total of a variable of any entity."""
    hw = array(sim, "household_weight", year).astype(np.float64)
    values = array(sim, variable, year).astype(np.float64)
    return float(np.sum(hw * to_household(sim, values, entity_of(sim, variable))))


def as_standard_reforms(reforms) -> list:
    """Accept parsed reforms or raw ``{name, parameters, ...}`` mappings."""
    reforms = list(reforms or [])
    if all(isinstance(r, StandardReform) for r in reforms):
        return reforms
    return parse_reforms({"reforms": reforms})


def measure_reforms(
    factory: Callable,
    baseline_parameters,
    baseline_balance: Mapping[int, float],
    baseline_targets: Mapping[int, Mapping[str, float]],
    reforms: Sequence[StandardReform],
    years: Sequence[int],
    rec: Recorder,
) -> list:
    """Cost each reform against the baseline run, and check it responds.

    Records each reform's change in gov_balance by year and, where the
    reform declares what it must move, the change in that variable's total
    and whether it moved enough in the right direction every year.

    First rebuilds an unreformed simulation the same way, which must
    reproduce the baseline exactly: otherwise reform costings would include
    differences that no reform caused.
    """
    outcomes = []
    first = years[0]
    try:
        fresh = factory(reform=None)
        again = weighted_total(fresh, "gov_balance", first)
        rec.check(
            "determinism:rebuilt_baseline",
            "A rebuilt unreformed simulation reproduces the baseline gov_balance exactly",
            again == baseline_balance[first],
            f"{fiscal_year_label(first)}: £{again:,.0f} against £{baseline_balance[first]:,.0f}",
            section="determinism",
        )
        del fresh
    except Exception as error:  # noqa: BLE001
        rec.check(
            "determinism:rebuilt_baseline",
            "A rebuilt unreformed simulation reproduces the baseline gov_balance exactly",
            False,
            f"{type(error).__name__}: {error}",
            section="determinism",
        )
    gc.collect()
    for reform in reforms:
        outcome = {
            "id": reform.id,
            "name": reform.name,
            "parameters": None,
            "responds": None,
            "error": None,
        }
        target_changes = {}
        try:
            parameters = reform_parameters(reform, baseline_parameters, years)
            outcome["parameters"] = parameters
            reformed = factory(reform=parameters)
            for year in years:
                rec.metric(
                    f"reforms.{reform.id}",
                    reform.name,
                    "reforms",
                    "gbp",
                    year,
                    weighted_total(reformed, "gov_balance", year)
                    - baseline_balance[year],
                )
                if reform.responds is not None:
                    variable = reform.responds.variable
                    change = (
                        weighted_total(reformed, variable, year)
                        - baseline_targets[year][variable]
                    )
                    target_changes[year] = change
                    rec.metric(
                        f"reform_targets.{reform.id}",
                        f"{reform.name}: change in {variable}",
                        "reform_targets",
                        "gbp",
                        year,
                        change,
                    )
            del reformed
        except Exception as error:  # noqa: BLE001 - one reform's failure is reported, not fatal
            outcome["error"] = f"{type(error).__name__}: {error}"
        if reform.responds is not None:
            outcome["responds"] = {
                "variable": reform.responds.variable,
                "direction": reform.responds.direction,
                "minimum": reform.responds.minimum,
            }
            if outcome["error"] is None:
                ok, detail = responsiveness(reform.responds, target_changes)
            else:
                ok, detail = False, "the reform did not run"
            rec.check(
                f"responsive:{reform.id}",
                f"'{reform.name}' moves {reform.responds.variable} "
                f"{reform.responds.direction} by at least "
                f"£{reform.responds.minimum / 1e9:,.2f}bn in every year",
                ok,
                detail,
                section="reforms",
            )
        gc.collect()
        outcomes.append(outcome)
    return outcomes


def measure(
    sim,
    factory: Callable,
    partition: Partition,
    spec: Spec,
    *,
    label: str,
    reforms: Sequence[Mapping] = (),
    run_guard: bool = True,
    provenance: Optional[Mapping] = None,
    guard_variables: Optional[Sequence[str]] = None,
) -> tuple:
    """Measure a simulation over the spec's horizon.

    ``sim`` is a fresh simulation on the dataset; ``factory(reform=None)``
    builds another on the same dataset. Returns ``(result, households)``.
    """
    started = time.time()
    timings = {}
    rec = Recorder()
    model_lists, list_problems = read_model_lists(partition)
    problems = list_problems + closure_problems(
        partition, model_lists, sim.tax_benefit_system.variables
    )
    rec.check(
        "closure",
        "Each model total's components are exactly the partition's heads and declared double counts",
        not problems,
        "; ".join(problems),
        section="partition",
    )
    snapshot = snapshot_inputs(sim, partition.component_variables())

    reforms = as_standard_reforms(reforms)
    target_variables = sorted({r.responds.variable for r in reforms if r.responds})
    households = {}
    baseline_balance, baseline_targets = {}, {}
    reset = getattr(sim, "_invalidate_all_caches", None)
    for year in spec.years:
        t = time.time()
        measure_year(sim, partition, spec, year, rec, households)
        baseline_balance[year] = weighted_total(sim, "gov_balance", year)
        baseline_targets[year] = {
            variable: weighted_total(sim, variable, year)
            for variable in target_variables
        }
        timings[f"year_{year}"] = round(time.time() - t, 2)
        if reset is not None:
            # Keep memory flat across the horizon; supplied inputs survive.
            reset()
            gc.collect()
    _finite_metrics_check(rec)

    guard = {"status": "skipped", "reason": "not requested"}
    if run_guard:
        t = time.time()
        guard = counted_once(
            sim,
            partition,
            spec.guard_year,
            spec.counted_once_tolerance,
            snapshot,
            active=active_parameters(sim, partition, spec.guard_year),
            variables_to_check=guard_variables,
        )
        timings["counted_once"] = round(time.time() - t, 2)
        for result in guard.get("components", []):
            if result["status"] == "skipped":
                continue
            rec.check(
                f"counted_once:{result['variable']}",
                f"Adding £1 to {result['variable']} adds exactly £1 to each tax total it is in, "
                "and at most £1 to each spending total",
                result["status"] == "pass",
                result["detail"],
                section="counted_once",
            )
        for result in guard.get("double_counts", []):
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
        if guard.get("status") == "skipped":
            rec.check(
                "counted_once:ran",
                "The counted-once check ran",
                False,
                guard.get("reason", ""),
                severity="warn",
                section="counted_once",
            )

    t = time.time()
    reform_outcomes = measure_reforms(
        factory,
        sim.tax_benefit_system.parameters,
        baseline_balance,
        baseline_targets,
        reforms,
        spec.years,
        rec,
    )
    timings["reforms"] = round(time.time() - t, 2)
    for outcome in reform_outcomes:
        rec.check(
            f"reform_runs:{outcome['id']}",
            f"The reform '{outcome['name']}' runs",
            outcome["error"] is None,
            outcome["error"] or "",
            section="reforms",
        )
    timings["total"] = round(time.time() - started, 2)

    result = {
        "schema": TOOL_SCHEMA,
        "status": "ok",
        "label": label,
        "years": spec.years,
        "provenance": dict(provenance or {}),
        "runtime": runtime_identity(),
        "partition": partition.as_dict(),
        "metrics": list(rec.metrics.values()),
        "checks": list(rec.checks.values()),
        "guard": guard,
        "reforms": reform_outcomes,
        "timings": timings,
    }
    return result, households


def write_result(out_dir, result: Mapping, households: Optional[Mapping] = None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "result.json", "w") as f:
        json.dump(result, f, indent=1, sort_keys=False, allow_nan=True)
    if households:
        arrays = {
            f"{year}__{name}": values
            for year, columns in households.items()
            for name, values in columns.items()
        }
        np.savez_compressed(out_dir / "households.npz", **arrays)


def read_result(out_dir) -> tuple:
    """Load ``(result, households)`` written by :func:`write_result`."""
    out_dir = Path(out_dir)
    path = out_dir / "result.json"
    if not path.exists():
        return None, None
    with open(path) as f:
        result = json.load(f)
    households = None
    npz = out_dir / "households.npz"
    if npz.exists():
        households = {}
        with np.load(npz) as data:
            for key in data.files:
                year, _, name = key.partition("__")
                households.setdefault(year, {})[name] = data[key]
    return result, households
