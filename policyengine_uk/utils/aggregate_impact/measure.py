"""Measure one model checkout on one dataset over the report horizon."""

from __future__ import annotations

import dataclasses
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

from .privacy import HIDDEN_KEY, MIN_CELL, small
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
        # The year being measured; a check records which scopes it failed
        # in, so a comparison can tell a newly failing year from an old one.
        self.scope: str = ""
        # Raw values of suppressed or rounded figures, and the suppressed heads
        # each protected total contains: kept off the record, written only to
        # private/ for the comparison (``write_result``).
        self.hidden: dict = {}
        self.contains: dict = {}

    def metric(
        self,
        metric_id,
        label,
        section,
        kind,
        year,
        value,
        group=None,
        unit=None,
        records=None,
    ):
        """Record a figure; ``records`` is how many records it is built from.

        A figure from fewer than ``MIN_CELL`` records (but more than none) is
        published as ``None`` and its year listed in ``suppressed``.
        """
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
        if records is not None and small(records):
            record["values"][str(year)] = None
            record.setdefault("suppressed", []).append(str(year))
            # Kept for complementary protection of totals; never published.
            self.hidden[(metric_id, str(year))] = float(value)
        else:
            record["values"][str(year)] = float(value)

    def check(
        self, check_id, label, ok, detail="", severity="fail", section="", scope=None
    ):
        """Record a check; repeated ids (one per year) merge into one result.

        ``failing`` maps each scope the check failed in (a year, or "" for a
        check that is not per year) to its detail. ``ok=None`` records that
        the check did not apply (``skipped``), which is not a pass.
        """
        if ok is None:
            status = "skipped"
        else:
            status = "pass" if ok else ("warn" if severity == "warn" else "fail")
        scope = self.scope if scope is None else scope
        record = self.checks.get(check_id)
        if record is None:
            record = {
                "id": check_id,
                "label": label,
                "section": section,
                "severity": severity,
                "status": status,
                "details": [],
                "failing": {},
            }
            self.checks[check_id] = record
        elif status in ("fail", "warn") and record["status"] in ("pass", "skipped"):
            record["status"] = status
        elif status == "pass" and record["status"] == "skipped":
            record["status"] = status
        if ok is None:
            if detail and detail not in record["details"]:
                record["details"].append(detail)
        elif not ok:
            record["failing"][scope] = detail
            if detail:
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


def _digest_tool_files() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.suffix in (".py", ".yaml") and "__pycache__" not in path.parts:
            digest.update(path.relative_to(root).as_posix().encode() + b"\0")
            digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


# Taken when this module loads, so a result is stamped with the code that
# produced it even if the files change while a measurement runs.
_TOOL_DIGEST = _digest_tool_files()


def tool_digest() -> str:
    """SHA-256 of this package's code and spec, independent of where it lives."""
    return _TOOL_DIGEST


def definitions_digest(spec: Spec, reforms: Sequence) -> str:
    """SHA-256 of what was actually measured: the effective spec and reforms.

    ``tool_digest`` covers the files as shipped; this covers a spec or reform
    set passed in instead, and a horizon overridden at the call.
    """
    parsed = {
        field.name: getattr(spec, field.name)
        for field in dataclasses.fields(spec)
        if field.name != "raw"
    }
    payload = {
        "spec": spec.raw,
        # The parsed fields too: a spec changed with dataclasses.replace
        # keeps its raw mapping.
        "parsed": parsed,
        "years": spec.years,
        "guard_year": spec.guard_year,
        "reforms": [
            {
                "id": r.id,
                "parameters": dict(r.parameters),
                "scale": dict(r.scale),
                "responds": None
                if r.responds is None
                else [r.responds.variable, r.responds.direction, r.responds.minimum],
            }
            for r in reforms
        ],
    }
    text = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(text.encode()).hexdigest()


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


# Results may be published, and the dataset is licensed survey microdata. A
# check's detail names how many records it concerns and their weighted total
# only when there are at least this many; below it, the detail says "fewer
# than" and gives no amount, so it never describes one or a few records.

# A geographic exclusivity guard treats a household value this small as zero:
# before the #2159 fix, expected_sdlt adds 0.045 to every household.
EXCLUSIVITY_ZERO_GBP = 0.05


def _weighted_records(mask, weight) -> int:
    """Units in ``mask`` that carry weight: a zero-weight record adds nothing.

    Sol re-review 3 of #2335: three weighted recipients and seven zero-weight
    records with values are three records, not ten.
    """
    return int(np.count_nonzero(np.asarray(mask) & (np.asarray(weight) > 0)))


def cell_detail(count: int, what: str, weighted: str) -> str:
    """``"N <what>, <weighted>"``, or ``"fewer than 10 <what>"`` for a small cell."""
    if count < MIN_CELL:
        return f"fewer than {MIN_CELL} {what}"
    return f"{count:,} {what}, {weighted}"


def _identity_check(rec, check_id, label, components_hh, total_hh, year, spec, weights):
    """Household-level accounting identity: components add up to the total.

    The detail gives counts and weighted totals only, and nothing at all
    about fewer than ``MIN_CELL`` households (see ``cell_detail``).
    """
    difference = components_hh - total_hh
    scale = np.abs(total_hh) + 1.0
    tolerance = 1.0 + spec.identity_relative_tolerance * scale
    bad = np.abs(difference) > tolerance
    finite = np.all(np.isfinite(difference))
    ok = bool(finite and not bad.any())
    detail = ""
    if not ok:
        gap = float(np.nansum(weights * np.where(bad, difference, 0.0)))
        detail = f"{fiscal_year_label(year)}: " + cell_detail(
            _weighted_records(bad, weights),
            "households differ",
            f"by a weighted £{gap:,.0f} in total",
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
            records=_weighted_records(values != 0, weights[entity]),
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
                records=_weighted_records(values > 0, weights[entity]),
            )
        if head.sign == "nonnegative":
            negative = values < -0.005
            rec.check(
                f"sign:{head.id}",
                f"{head.label} is never negative",
                not bool(negative.any()),
                f"{fiscal_year_label(year)}: "
                + cell_detail(
                    _weighted_records(negative, weights[entity]),
                    "units below zero",
                    f"a weighted £{float(np.sum(hw * np.where(hh < 0, hh, 0.0))):,.0f} in total",
                ),
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
    # Geographic exclusivity, on the data. A declared double count is netted
    # out of the head that contains it, and tiny values count as zero, so the
    # guard sees each nation's own tax even before the #2159 fix.
    variable_of = {head.id: head.variable for head in partition.heads}
    for guard in partition.overlap_guards:
        if (
            not isinstance(guard, Mapping)
            or guard.get("kind") != "geographic_exclusivity"
        ):
            continue
        members = [variable_of[h] for h in guard.get("heads") or []]
        nonzero = np.zeros_like(hw, dtype=int)
        for variable in members:
            own = head_hh[variable].copy()
            for dc in partition.double_counts:
                if dc.contained_in == variable:
                    own = own - double_count_hh[dc.variable]
            nonzero = nonzero + (np.abs(own) > EXCLUSIVITY_ZERO_GBP).astype(int)
        overlapping = nonzero > 1
        rec.check(
            f"overlap_guard:{guard.get('id')}",
            "At most one of " + ", ".join(members) + " is non-zero for any household",
            not bool(overlapping.any()),
            f"{fiscal_year_label(year)}: "
            + cell_detail(
                _weighted_records(overlapping, hw),
                "households have more than one",
                f"a weighted {float(np.sum(hw * overlapping)):,.0f}",
            ),
            section="partition",
        )

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
            hw,
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
            hw,
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
            hw,
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
        rec.check(
            f"available:{measure_spec['id']}",
            f"{measure_spec['label']} can be computed",
            True,
            section="coverage",
        )
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
                rec.check(
                    f"available:{group['id']}",
                    f"{group['label']} can be identified",
                    True,
                    section="coverage",
                )
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
    protect_totals(rec, partition, active, year)
    hidden = households.setdefault(HIDDEN_KEY, {"values": {}, "contains": {}})
    detail = hidden_detail(rec, year)
    hidden["values"].update(detail["values"])
    hidden["contains"].update(detail["contains"])
    households[str(year)] = {
        "household_id": array(sim, "household_id", year).astype(np.int64),
        "household_weight": hw.astype(np.float64),
        "household_count_people": people.astype(np.float64),
        "decile": decile,
        "income": income,
    }


# A total that contains a suppressed head is rounded to this, so the head
# cannot be recovered by subtracting the published heads from it; a head
# worth half this or more makes the total suppressed instead.
TOTAL_ROUNDING_GBP = 1e9
# In a year with a suppressed head, each decile's mean household income is
# rounded to this: an error of up to £500 a household, about £1.4bn over a
# decile of 2.8m households, more than the £0.5bn a rounded total can hide.
DECILE_MEAN_ROUNDING_GBP = 1e3


def total_components(partition: Partition, active) -> dict:
    """The heads each published total is built from."""

    def heads(*totals):
        return {h.id for t in totals for h in partition.heads_in(t, active)}

    out = {f"model.{t}": heads(t) for t in partition.totals}
    out["balance.receipts"] = heads("gov_tax")
    out["balance.spending"] = heads("gov_spending")
    out["balance.balance"] = heads("gov_tax", "gov_spending")
    out["balance.household_only_benefits"] = {
        h.id
        for h in partition.spending_heads
        if "household_benefits" in h.totals and "gov_spending" not in h.totals
    }
    out["model.gov_balance"] = heads("gov_tax", "gov_spending")
    every = {h.id for h in partition.heads}
    for variable in HOUSEHOLD_TOTALS:
        out[f"household.{variable}"] = every
    return out


def protect_totals(rec: "Recorder", partition: Partition, active, year: int) -> None:
    """Complementary protection: totals cannot reveal a suppressed head.

    A head from fewer than ``MIN_CELL`` records is published as None, but a
    total containing it, less the published heads, would give it back. Each
    such total is rounded to ``TOTAL_ROUNDING_GBP`` for that year, or
    suppressed if a contained head is worth half that or more.
    """
    key = str(year)
    hidden = {
        metric_id.split(".", 1)[1]: abs(value)
        for (metric_id, y), value in rec.hidden.items()
        if y == key and metric_id.split(".", 1)[0] in ("receipts", "spending")
    }
    if not hidden:
        return
    for metric_id, heads in total_components(partition, active).items():
        record = rec.metrics.get(metric_id)
        contained = [hidden[h] for h in heads if h in hidden]
        if record is None or not contained or record["values"].get(key) is None:
            continue
        value = record["values"][key]
        rec.hidden[(metric_id, key)] = float(value)
        rec.contains[(metric_id, key)] = sorted(
            f"{section}.{h}"
            for h in heads
            if h in hidden
            for section in ("receipts", "spending")
            if (f"{section}.{h}", key) in rec.hidden
        )
        if max(contained) >= TOTAL_ROUNDING_GBP / 2:
            record["values"][key] = None
            record.setdefault("suppressed", []).append(key)
        else:
            record["values"][key] = float(
                round(value / TOTAL_ROUNDING_GBP) * TOTAL_ROUNDING_GBP
            )
            record.setdefault("rounded", []).append(key)
    # Each decile's mean income, times its share of households, would rebuild
    # the household income total that was just rounded.
    for d in range(1, 11):
        record = rec.metrics.get(f"deciles.mean_income.{d}")
        if record is None or record["values"].get(key) is None:
            continue
        value = record["values"][key]
        rec.hidden[(record["id"], key)] = float(value)
        # Household income contains every head.
        rec.contains[(record["id"], key)] = sorted(
            m
            for (m, y) in rec.hidden
            if y == key and m.split(".", 1)[0] in ("receipts", "spending")
        )
        record["values"][key] = float(
            round(value / DECILE_MEAN_ROUNDING_GBP) * DECILE_MEAN_ROUNDING_GBP
        )
        record.setdefault("rounded", []).append(key)


def hidden_detail(rec: "Recorder", year: int) -> dict:
    """One year's raw protected values and containment, for ``private/`` only.

    Keys are ``"<metric id>|<year>"``. ``values`` holds the raw value of every
    suppressed or rounded figure; ``contains`` lists, for each protected
    total, the suppressed heads inside it. ``compare.private_delta`` reads
    them to publish a protected total's exact change when it is safe.
    """
    key = str(year)
    return {
        "values": {f"{m}|{y}": v for (m, y), v in rec.hidden.items() if y == key},
        "contains": {
            f"{m}|{y}": list(heads)
            for (m, y), heads in rec.contains.items()
            if y == key
        },
    }


def publishable_guard(guard: dict) -> dict:
    """The counted-once result with small cells removed (privacy.py).

    A component perturbed in fewer than ``MIN_CELL`` units keeps no count, no
    responses or coefficients, and no weighted shares in its problems. A
    problem or mediated response in fewer than ``MIN_CELL`` households keeps
    no count and no share. Messages already say "fewer than 10".
    """
    out = dict(guard)
    components = []
    for row in guard.get("components") or []:
        row = dict(row)
        few_units = small(row.get("units") or 0)
        if few_units:
            # How the heads responded to so few units says what those
            # recipients receive (Sol re-review 3 of #2335).
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
                cleaned.append(item)
            row[key] = cleaned
        components.append(row)
    if "components" in guard:
        out["components"] = components
    return out


def _finite_metrics_check(rec: Recorder):
    bad = [
        f"{m['id']} {fiscal_year_label(int(year))}"
        for m in rec.metrics.values()
        for year, value in m["values"].items()
        if year not in m.get("suppressed", ()) and not np.isfinite(value)
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
    try:
        fresh = factory(reform=None)
        for year in years:
            again = weighted_total(fresh, "gov_balance", year)
            rec.check(
                "determinism:rebuilt_baseline",
                "A rebuilt unreformed simulation reproduces the baseline gov_balance exactly",
                again == baseline_balance[year],
                # No amounts: an exact gov_balance, less the published heads,
                # would give a suppressed head back (Sol re-review 3 of #2335).
                f"{fiscal_year_label(year)}: the rebuilt baseline's gov_balance "
                "differs from the first run's",
                section="determinism",
                scope=str(year),
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
            label = (
                f"'{reform.name}' moves {reform.responds.variable} "
                f"{reform.responds.direction} by at least "
                f"£{reform.responds.minimum / 1e9:,.2f}bn in every year"
            )
            if outcome["error"] is not None:
                for year in years:
                    rec.check(
                        f"responsive:{reform.id}",
                        label,
                        False,
                        f"{fiscal_year_label(year)}: the reform did not run",
                        section="reforms",
                        scope=str(year),
                    )
            else:
                # One verdict per year, so a newly inert year is a regression
                # even when another year already failed.
                for year in years:
                    ok, detail = responsiveness(
                        reform.responds, {year: target_changes.get(year, float("nan"))}
                    )
                    rec.check(
                        f"responsive:{reform.id}",
                        label,
                        ok,
                        detail,
                        section="reforms",
                        scope=str(year),
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
    closure_label = (
        "Each model total's components are exactly the partition's heads and "
        "declared double counts"
    )
    rec.check("closure", closure_label, True, section="partition", scope="")
    # One scope per problem: its text names the total and the variable.
    for problem_text in problems:
        rec.check(
            "closure",
            closure_label,
            False,
            problem_text,
            section="partition",
            scope=problem_text,
        )
    snapshot = snapshot_inputs(sim, partition.component_variables())

    reforms = as_standard_reforms(reforms)
    target_variables = sorted({r.responds.variable for r in reforms if r.responds})
    households = {}
    baseline_balance, baseline_targets = {}, {}
    reset = getattr(sim, "_invalidate_all_caches", None)
    for year in spec.years:
        t = time.time()
        rec.scope = str(year)
        measure_year(sim, partition, spec, year, rec, households)
        rec.scope = ""
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
            check_id = f"counted_once:{result['variable']}"
            label = (
                f"Raising {result['variable']} by £1 raises its own head by £1, moves no "
                "other tax head and raises no other benefit"
            )
            if result["status"] != "fail":
                rec.check(
                    check_id,
                    label,
                    None if result["status"] == "skipped" else True,
                    result["detail"],
                    section="counted_once",
                    scope="",
                )
            # One scope per failing (total, head, kind), so a comparison sees
            # a head that newly contains the component, not just "still fails".
            for item in result.get("problems") or []:
                rec.check(
                    check_id,
                    label,
                    False,
                    item["message"],
                    section="counted_once",
                    scope=f"{item['total']}:{item['head']}:{item['kind']}",
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
        rec.check(
            "counted_once:ran",
            "The counted-once check ran",
            guard.get("status") == "ran",
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
    # After the reform costings, so that they are covered too.
    _finite_metrics_check(rec)
    timings["total"] = round(time.time() - started, 2)

    provenance = dict(provenance or {})
    provenance["tool_sha256"] = tool_digest()
    provenance["definitions_sha256"] = definitions_digest(spec, reforms)
    provenance["metrics_version"] = (
        f"{TOOL_SCHEMA}+{provenance['tool_sha256'][:16]}"
        f"+{provenance['definitions_sha256'][:16]}"
    )
    result = {
        "schema": TOOL_SCHEMA,
        "status": "ok",
        "label": label,
        "years": spec.years,
        "provenance": provenance,
        "runtime": runtime_identity(),
        "partition": partition.as_dict(),
        "metrics": list(rec.metrics.values()),
        "checks": list(rec.checks.values()),
        "guard": publishable_guard(guard),
        "reforms": reform_outcomes,
        "timings": timings,
    }
    return result, households


PRIVATE_DIRECTORY = "private"
HOUSEHOLDS_FILE = "households.npz"
HIDDEN_FILE = "hidden.json"


def write_result(out_dir, result: Mapping, households: Optional[Mapping] = None):
    """Write the aggregates to result.json and household detail to private/.

    ``result.json`` holds only aggregates and may be published. Everything
    under ``private/`` is household-level detail from licensed microdata: it
    exists for the decile comparison and must never be uploaded or shared.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "result.json", "w") as f:
        json.dump(result, f, indent=1, sort_keys=False, allow_nan=True)
    if households:
        arrays = {
            f"{year}__{name}": values
            for year, columns in households.items()
            if year != HIDDEN_KEY
            for name, values in columns.items()
        }
        private = out_dir / PRIVATE_DIRECTORY
        private.mkdir(exist_ok=True)
        np.savez_compressed(private / HOUSEHOLDS_FILE, **arrays)
        if HIDDEN_KEY in households:
            with open(private / HIDDEN_FILE, "w") as f:
                json.dump(households[HIDDEN_KEY], f)


def read_result(out_dir) -> tuple:
    """Load ``(result, households)`` written by :func:`write_result`."""
    out_dir = Path(out_dir)
    path = out_dir / "result.json"
    if not path.exists():
        return None, None
    with open(path) as f:
        result = json.load(f)
    households = None
    npz = out_dir / PRIVATE_DIRECTORY / HOUSEHOLDS_FILE
    if npz.exists():
        households = {}
        with np.load(npz) as data:
            for key in data.files:
                year, _, name = key.partition("__")
                households.setdefault(year, {})[name] = data[key]
        hidden = out_dir / PRIVATE_DIRECTORY / HIDDEN_FILE
        if hidden.exists():
            with open(hidden) as f:
                households[HIDDEN_KEY] = json.load(f)
    return result, households
