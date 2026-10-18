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

from .privacy import MIN_CELL, count_text, small
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
        # Raw values of suppressed heads: kept off the record, used only to
        # take them out of the totals that contain them.
        self.hidden: dict = {}

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


def _identity_check(
    rec,
    check_id,
    label,
    components_hh,
    total_hh,
    year,
    spec,
    weights,
    leave_out=None,
):
    """Household-level accounting identity: components add up to the total.

    The detail gives counts and weighted totals only, and nothing at all
    about fewer than ``MIN_CELL`` households (see ``cell_detail``).

    ``leave_out`` marks the households holding a component suppressed this
    year, which aren't checked: with a formula that scales its components,
    whether, and by how much, they differ would depend on the suppressed
    values (Sol re-review 7 of #2335). The verdict and the detail then come
    from the other households only.
    """
    difference = components_hh - total_hh
    scale = np.abs(total_hh) + 1.0
    tolerance = 1.0 + spec.identity_relative_tolerance * scale
    checked = np.ones_like(difference, dtype=bool) if leave_out is None else ~leave_out
    bad = (np.abs(difference) > tolerance) & checked
    finite = np.all(np.isfinite(difference[checked]))
    ok = bool(finite and not bad.any())
    detail = ""
    if not ok:
        gap = float(np.nansum(weights * np.where(bad, difference, 0.0)))
        detail = f"{fiscal_year_label(year)}: " + cell_detail(
            _weighted_records(bad, weights),
            "households differ",
            f"by a weighted £{gap:,.0f} in total",
        )
        if leave_out is not None:
            detail += (
                f" (households holding a figure from fewer than {MIN_CELL} "
                "records aren't checked this year)"
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
        records = _weighted_records(values != 0, weights[entity])
        rec.check(
            f"finite:{head.id}",
            f"{head.label} is finite for every unit",
            bool(finite.all()),
            # No count of fewer than 10 units (Sol re-review 8 of #2335).
            f"{fiscal_year_label(year)}: "
            + count_text(int((~finite).sum()), "non-finite values"),
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
            records=records,
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
                # Suppressed with its head: a caseload of zero would say that
                # none of the head's few records is positive.
                records=1
                if small(records)
                else _weighted_records(values > 0, weights[entity]),
            )
        if head.sign == "nonnegative" and small(records):
            # Whether any of so few records is negative is about them alone
            # (Sol re-review 8 of #2335): not checked this year.
            rec.check(
                f"sign:{head.id}",
                f"{head.label} is never negative",
                None,
                f"{fiscal_year_label(year)}: not checked, from fewer than "
                f"{MIN_CELL} records",
                section="signs",
            )
        elif head.sign == "nonnegative":
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
            # Like a head: from fewer than 10 records it is suppressed (Sol
            # re-review 7 of #2335).
            records=_weighted_records(
                values != 0, weights[entity_of(sim, dc.variable)]
            ),
        )
    hidden = suppressed_components(rec, partition, year)
    # Households holding a suppressed component: no check verdict or detail
    # may depend on them this year.
    holding = None
    if hidden:
        holding = np.zeros(len(hw), dtype=bool)
        for variable in hidden:
            holding |= {**head_hh, **double_count_hh}[variable] != 0

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
        if holding is not None:
            # A holder's verdict would depend on the suppressed figure (Sol
            # re-review 8 of #2335), as for the identities.
            overlapping &= ~holding
        rec.check(
            f"overlap_guard:{guard.get('id')}",
            "At most one of " + ", ".join(members) + " is non-zero for any household",
            not bool(overlapping.any()),
            f"{fiscal_year_label(year)}: "
            + cell_detail(
                _weighted_records(overlapping, hw),
                "households have more than one",
                f"a weighted {float(np.sum(hw * overlapping)):,.0f}",
            )
            + (
                f" (households holding a figure from fewer than {MIN_CELL} "
                "records aren't checked this year)"
                if holding is not None
                else ""
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
            leave_out=holding,
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
            leave_out=holding,
        )
    for variable, label in HOUSEHOLD_TOTALS.items():
        if variable in tbs_variables:
            values = array(sim, variable, year).astype(np.float64)
            excludes = None
            if variable == "hbai_household_net_income" and hidden:
                values, excludes = _hbai_without(sim, year, hidden, holding)
            metric_id = f"household.{variable}"
            if values is None:
                # The suppressed components can't be taken out of this total.
                _publish_suppressed(rec, metric_id, label, "household_totals", year)
                continue
            rec.metric(
                metric_id,
                label,
                "household_totals",
                "gbp",
                year,
                float(np.sum(hw * values)),
            )
            if excludes:
                _exclude(rec.metrics[metric_id], str(year), excludes)
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
            leave_out=holding,
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

    net_income, net_income_excludes = rebuild_protected(
        rec,
        partition,
        active,
        hidden,
        {**head_hh, **double_count_hh},
        hw,
        year,
        market_hh=(
            array(sim, "household_market_income", year).astype(np.float64)
            if "household_market_income" in tbs_variables
            else None
        ),
        pension_hh=(
            to_household(
                sim,
                array(sim, "pension_contributions", year).astype(np.float64),
                entity_of(sim, "pension_contributions"),
            )
            if "pension_contributions" in tbs_variables
            else None
        ),
    )
    decile = array(sim, spec.decile_variable, year).astype(np.int64)
    income = array(sim, spec.income_variable, year).astype(np.float64)
    income_excludes = {}
    ranking_holds_hidden = bool(hidden) and hbai_holds_any(hidden)
    if ranking_holds_hidden:
        # Households are ranked into deciles on HBAI income, which holds a
        # suppressed component this year: which decile its holders fall in
        # depends on it, so no decile figure is published.
        income = None
        for d in range(1, 11):
            rec.metric(
                f"deciles.mean_income.{d}",
                f"Decile {d}: mean {spec.income_variable} per household",
                "deciles",
                "gbp_household",
                year,
                float("nan"),
                group="Own-decile levels",
                records=1,  # published as suppressed (privacy.py)
            )
    elif net_income_excludes:
        if spec.income_variable == "household_net_income" and net_income is not None:
            income, income_excludes = net_income, net_income_excludes
        else:
            income = None  # its suppressed parts can't be taken out of it
    for d in range(1, 11) if income is not None else ():
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
        if income_excludes:
            _exclude(
                rec.metrics[f"deciles.mean_income.{d}"], str(year), income_excludes
            )
    if ranking_holds_hidden:
        # Poverty and inequality are measured on HBAI income, which holds a
        # suppressed component this year; a Gini or poverty count with the
        # totals published could give it back (Sol re-review 6 of #2335).
        for record in rec.metrics.values():
            if record["section"] in ("poverty", "poverty_count", "inequality"):
                if record["values"].get(str(year)) is not None:
                    record["values"][str(year)] = None
                    record.setdefault("suppressed", []).append(str(year))
    if income is not None:
        households[str(year)] = {
            "household_id": array(sim, "household_id", year).astype(np.int64),
            "household_weight": hw.astype(np.float64),
            "household_count_people": people.astype(np.float64),
            "decile": decile,
            "income": income,
            # The suppressed components the income leaves out: both sides
            # must leave out the same ones for their decile rows to compare.
            "excludes": np.array(sorted(income_excludes), dtype=str),
        }


def _exclude(record: dict, key: str, excludes: Mapping) -> None:
    """Record which suppressed components a figure leaves out in ``key``."""
    # Rebound rather than written through, which the cached-array scan
    # (test_cached_arrays_not_written_in_place) would read as an array write.
    record["excludes"] = {**(record.get("excludes") or {}), key: dict(excludes)}


def suppressed_components(rec: "Recorder", partition: Partition, year: int) -> dict:
    """``{variable: (metric id, raw value)}`` for each head or declared double
    count suppressed in ``year``."""
    key = str(year)
    out = {}
    for head in partition.heads:
        metric_id = f"{'receipts' if head.kind == 'tax' else 'spending'}.{head.id}"
        if (metric_id, key) in rec.hidden:
            out[head.variable] = (metric_id, rec.hidden[(metric_id, key)])
    for dc in partition.double_counts:
        metric_id = f"double_counts.{dc.variable}"
        if (metric_id, key) in rec.hidden:
            out[dc.variable] = (metric_id, rec.hidden[(metric_id, key)])
    return out


def rebuild_protected(
    rec: "Recorder",
    partition: Partition,
    active,
    hidden: Mapping,
    component_hh: Mapping,
    hw: np.ndarray,
    year: int,
    market_hh=None,
    pension_hh=None,
) -> tuple:
    """Publish each total that holds a suppressed component rebuilt without it.

    The total is rebuilt household by household from its other components,
    never as the model's total less the suppressed one, so no published
    figure depends on a suppressed component's values: not through a formula
    that scales its components, and not through an identity's tolerance (Sol
    re-reviews 5 to 7 of #2335). Each rebuilt figure is:

    - a model total: its other heads and declared double counts;
    - a balance aggregate: its other heads;
    - ``gov_balance``: the rebuilt ``gov_tax`` less the rebuilt
      ``gov_spending``;
    - household net income: market income plus the rebuilt
      ``household_benefits``, less the rebuilt ``household_tax`` and pension
      contributions (its own adds and subtracts). Suppressed if market
      income or pension contributions aren't available.

    Its record lists the left-out components, with the sign each enters
    with, under ``excludes``. Returns the rebuilt household net income per
    household (None if not rebuilt) and what it leaves out, for the deciles.
    """
    if not hidden:
        return None, {}
    key = str(year)

    def parts(total, sign=1, double_counts=True):
        out = [(h.variable, sign) for h in partition.heads_in(total, active)]
        if double_counts:
            out += [
                (d.variable, sign) for d in partition.double_counts_in(total, active)
            ]
        return out

    def rebuilt(signed_parts):
        """``(per-household sum of the published parts, excludes)``, or None
        when no part is suppressed."""
        if not any(variable in hidden for variable, _ in signed_parts):
            return None
        total = np.zeros_like(hw, dtype=np.float64)
        excludes = {}
        for variable, sign in signed_parts:
            if variable in hidden:
                metric_id = hidden[variable][0]
                excludes[metric_id] = excludes.get(metric_id, 0) + sign
            else:
                total = total + sign * component_hh[variable]
        return total, {m: sign for m, sign in excludes.items() if sign}

    def publish(metric_id, result):
        record = rec.metrics.get(metric_id)
        if result is None or record is None or record["values"].get(key) is None:
            return
        values, excludes = result
        record["values"][key] = float(np.sum(hw * values))
        if excludes:
            _exclude(record, key, excludes)

    for total in partition.totals:
        publish(f"model.{total}", rebuilt(parts(total)))
    receipts = parts("gov_tax", double_counts=False)
    spending = parts("gov_spending", -1, double_counts=False)
    publish("balance.receipts", rebuilt(receipts))
    publish("balance.spending", rebuilt([(v, 1) for v, _ in spending]))
    publish("balance.balance", rebuilt(receipts + spending))
    publish(
        "balance.household_only_benefits",
        rebuilt(
            [
                (h.variable, 1)
                for h in partition.spending_heads
                if "household_benefits" in h.totals and "gov_spending" not in h.totals
            ]
        ),
    )
    publish("model.gov_balance", rebuilt(parts("gov_tax") + parts("gov_spending", -1)))

    net = rebuilt(parts("household_benefits") + parts("household_tax", -1))
    if net is None:
        return None, {}
    record = rec.metrics.get("household.household_net_income")
    if market_hh is None or pension_hh is None:
        if record is not None and record["values"].get(key) is not None:
            record["values"][key] = None
            record.setdefault("suppressed", []).append(key)
        return None, net[1]
    income = market_hh + net[0] - pension_hh
    publish("household.household_net_income", (income, net[1]))
    return income, net[1]


def _hbai_lists():
    """The HBAI income component lists, or None if the model has none."""
    try:
        from policyengine_uk.variables.household.income import (
            hbai_household_net_income as hbai,
        )

        return (
            set(hbai.HBAI_HOUSEHOLD_NET_INCOME_ADDS),
            set(hbai.HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS),
        )
    except (ImportError, AttributeError):
        return None


def hbai_holds_any(hidden: Mapping) -> bool:
    """Whether a suppressed component is part of HBAI income (True if unknown)."""
    lists = _hbai_lists()
    if lists is None:
        return True
    adds, subtracts = lists
    return any(variable in adds or variable in subtracts for variable in hidden)


# How far, per household, the HBAI component lists may be from the model's
# income before the reset: half a penny, the precision of the published
# figures. The rebuilt total never uses a suppressed component, so this bounds
# only a wrong figure (a component the model leaves out under the current
# policy), never a disclosure (Sol re-review 7 of #2335).
HBAI_REPRODUCTION_GBP = 0.005


def _hbai_without(sim, year, hidden, holding=None):
    """The HBAI household net income without the suppressed components, or None.

    Rebuilt household by household from its component lists without the
    suppressed ones, then reset at zero as HBAI does: it never uses their
    values. The lists must reproduce the model's income before the reset
    (``HBAI_REPRODUCTION_GBP``) for every household not in ``holding`` (those
    holding a suppressed component, whose verdict would depend on it), or
    the total is suppressed (None): a component the model leaves out under
    the current policy (council tax when it is abolished, say) would
    otherwise come back in (Sol re-reviews 6 and 7 of #2335). None also when
    the model doesn't expose the income before the reset or the lists.
    """
    lists = _hbai_lists()
    if lists is None:
        return None, None
    adds, subtracts = lists
    inside = {
        variable: 1 if variable in adds else -1
        for variable in hidden
        if variable in adds or variable in subtracts
    }
    values = array(sim, "hbai_household_net_income", year).astype(np.float64)
    if not inside:
        return values, None
    name = "hbai_household_net_income_before_reset_to_zero"
    variables = sim.tax_benefit_system.variables
    if name not in variables:
        return None, None
    before = array(sim, name, year).astype(np.float64)
    rebuilt = np.zeros_like(before)
    without = np.zeros_like(before)
    for variable, sign in [(v, 1) for v in sorted(adds)] + [
        (v, -1) for v in sorted(subtracts)
    ]:
        if variable in variables:
            part = array(sim, variable, year, map_to="household").astype(np.float64)
            rebuilt = rebuilt + sign * part
            if variable not in inside:
                without = without + sign * part
    checked = slice(None) if holding is None else ~np.asarray(holding)
    if not np.all(np.abs(rebuilt - before)[checked] <= HBAI_REPRODUCTION_GBP):
        return None, None
    excludes = {hidden[v][0]: sign for v, sign in inside.items()}
    return np.maximum(0.0, without), excludes


def _publish_suppressed(rec: "Recorder", metric_id, label, section, year):
    record = rec.metrics.setdefault(
        metric_id,
        {
            "id": metric_id,
            "label": label,
            "section": section,
            "group": None,
            "kind": "gbp",
            "unit": None,
            "values": {},
        },
    )
    record["values"][str(year)] = None
    record.setdefault("suppressed", []).append(str(year))


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
    # A declared double count's coefficient is its container's mean response
    # across its units: for fewer than MIN_CELL units it goes too (Sol
    # re-review 8 of #2335).
    units = {
        row.get("variable"): row.get("units") for row in guard.get("components") or []
    }
    double_counts = []
    for row in guard.get("double_counts") or []:
        row = dict(row)
        if small(units.get(row.get("variable")) or 0):
            row["coefficient"] = None
            if row.get("status") != "pass":
                row["detail"] = (
                    f"{row['contained_in']} no longer moves one for one with "
                    f"{row['variable']} (fewer than {MIN_CELL} units): the model "
                    "no longer counts it twice, so remove the declaration and give "
                    "it its own head"
                )
        double_counts.append(row)
    if "double_counts" in guard:
        out["double_counts"] = double_counts
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


# A record's income or tax changes when it moves by more than half a penny,
# as for decile rows (compare.decile_impacts).
CHANGE_GBP = 0.005


def baseline_records(sim, partition: Partition, rec: "Recorder", year: int, targets):
    """What the reform checks need from the baseline run in ``year``: each
    suppressed component's values, each household's gov_balance and each
    target variable's values. Kept in memory only, never written."""
    return {
        "hidden": {
            variable: array(sim, variable, year).astype(np.float64).copy()
            for variable in suppressed_components(rec, partition, year)
        },
        "household_weight": array(sim, "household_weight", year)
        .astype(np.float64)
        .copy(),
        "balance": to_household(
            sim,
            array(sim, "gov_balance", year).astype(np.float64),
            entity_of(sim, "gov_balance"),
        ).copy(),
        "targets": {
            variable: array(sim, variable, year).astype(np.float64).copy()
            for variable in targets
        },
    }


def reform_withheld(
    reformed, year: int, baseline: Optional[Mapping], components
) -> bool:
    """Whether a reform's costing and target change for ``year`` are withheld.

    They would be built from a small cell (Sol re-review 7 of #2335) when the
    reform:

    - changes any record of a component suppressed in the baseline, by any
      amount, even if the changes cancel nationally: they still move other
      figures (the tax on one recipient's pension, say). An unchanged record
      compares equal, because a rebuilt baseline reproduces the first run
      exactly (``determinism:rebuilt_baseline``); noise could only withhold
      more;
    - leaves any other component with 1 to 9 records (``privacy.small``),
      whose change would give that new small cell back;
    - changes gov_balance in 1 to 9 households, or a target variable in 1 to
      9 records, by more than ``CHANGE_GBP``: the change is theirs alone, as
      for a decile row.

    Withheld too when there is no baseline record for the year.
    """
    if baseline is None:
        return True
    for variable, before in baseline["hidden"].items():
        if not np.array_equal(
            array(reformed, variable, year).astype(np.float64), before
        ):
            return True
    weights = {}

    def weight(variable):
        entity = entity_of(reformed, variable)
        if entity not in weights:
            weights[entity] = array(reformed, f"{entity}_weight", year).astype(
                np.float64
            )
        return weights[entity]

    for variable in components:
        if variable in baseline["hidden"]:
            continue
        values = array(reformed, variable, year).astype(np.float64)
        if small(_weighted_records(values != 0, weight(variable))):
            return True
    balance = to_household(
        reformed,
        array(reformed, "gov_balance", year).astype(np.float64),
        entity_of(reformed, "gov_balance"),
    )
    changed = np.abs(balance - baseline["balance"]) > CHANGE_GBP
    if small(_weighted_records(changed, baseline["household_weight"])):
        return True
    for variable, before in baseline["targets"].items():
        after = array(reformed, variable, year).astype(np.float64)
        if small(
            _weighted_records(np.abs(after - before) > CHANGE_GBP, weight(variable))
        ):
            return True
    return False


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
    baseline: Optional[Mapping[int, Mapping]] = None,
    components: Sequence[str] = (),
) -> list:
    """Cost each reform against the baseline run, and check it responds.

    Records each reform's change in gov_balance by year and, where the
    reform declares what it must move, the change in that variable's total
    and whether it moved enough in the right direction every year.

    ``baseline`` gives, for each year, the baseline's records
    (``baseline_records``), and ``components`` the partition's component
    variables. A year whose figures would come from a small cell
    (``reform_withheld``) publishes neither the costing nor the target
    change, and its responsiveness detail gives no amount: a 10% uplift's
    cost of £100 would give back a suppressed £1,000 (Sol re-reviews 6 and 7
    of #2335). Without ``baseline``, every year is withheld.

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
        hidden_years = set()
        try:
            parameters = reform_parameters(reform, baseline_parameters, years)
            outcome["parameters"] = parameters
            reformed = factory(reform=parameters)
            for year in years:
                withheld = reform_withheld(
                    reformed, year, (baseline or {}).get(year), components
                )
                if withheld:
                    hidden_years.add(year)
                # records=1 publishes the figure as suppressed (privacy.py).
                records = 1 if withheld else None
                rec.metric(
                    f"reforms.{reform.id}",
                    reform.name,
                    "reforms",
                    "gbp",
                    year,
                    weighted_total(reformed, "gov_balance", year)
                    - baseline_balance[year],
                    records=records,
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
                        records=records,
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
                    if year in hidden_years and not ok:
                        detail = (
                            f"{fiscal_year_label(year)}: {reform.responds.variable} did "
                            "not move enough (the amount is withheld: it comes from "
                            f"fewer than {MIN_CELL} records)"
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
    baseline_balance, baseline_targets, baseline = {}, {}, {}
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
        # So that reform figures from a small cell are withheld.
        baseline[year] = baseline_records(sim, partition, rec, year, target_variables)
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
        # Details from the published guard, with small cells removed.
        for result in publishable_guard(guard).get("double_counts", []):
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
        baseline=baseline,
        components=partition.component_variables(),
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
            for name, values in columns.items()
        }
        private = out_dir / PRIVATE_DIRECTORY
        private.mkdir(exist_ok=True)
        np.savez_compressed(private / HOUSEHOLDS_FILE, **arrays)


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
    return result, households
