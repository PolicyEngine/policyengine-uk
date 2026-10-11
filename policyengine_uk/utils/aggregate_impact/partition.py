"""The fiscal partition: loading, structural validation and closure checks.

The partition lives with the model at
``policyengine_uk/data/fiscal_partition.yaml`` (schema 1; its header defines
the fields). This module reads the YAML directly, not through any loader in
the model, so the pull request head's copy of this tool can read the base
checkout's partition.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Optional

import yaml

SUPPORTED_SCHEMA_VERSIONS = {1}
PARTITION_RELATIVE_PATH = Path("data") / "fiscal_partition.yaml"
ENTITIES = {"person", "benunit", "household"}
SIGNS = {None, "nonnegative", "any"}

# Where each total's component list lives in the model, and which kind of
# heads it divides into. A total in the file may override these.
KNOWN_TOTALS = {
    "gov_tax": ("tax", "policyengine_uk.variables.gov.gov_tax", "GOV_TAX_VARIABLES"),
    "household_tax": (
        "tax",
        "policyengine_uk.variables.gov.hmrc.household_tax",
        "HOUSEHOLD_TAX_VARIABLES",
    ),
    "pre_budget_change_household_tax": (
        "tax",
        "policyengine_uk.variables.contrib.policyengine.pre_budget_change_household_tax",
        "PRE_BUDGET_CHANGE_HOUSEHOLD_TAX_VARIABLES",
    ),
    "gov_spending": (
        "spending",
        "policyengine_uk.variables.gov.gov_spending",
        "GOV_SPENDING_VARIABLES",
    ),
    "household_benefits": (
        "spending",
        "policyengine_uk.variables.household.income.household_benefits",
        "HOUSEHOLD_BENEFIT_VARIABLES",
    ),
}
GOVERNMENT_TOTALS = {"gov_tax", "gov_spending"}


class PartitionError(ValueError):
    """The partition file is malformed or internally inconsistent."""


@dataclass(frozen=True)
class TotalSpec:
    name: str
    kind: str  # "tax" or "spending"
    module: str
    list_name: str
    label: str = ""
    dropped_when: tuple = ()  # ((parameter path, (variable, ...)), ...)


@dataclass(frozen=True)
class Head:
    id: str
    label: str
    variable: str
    totals: tuple
    report_group: str
    kind: str  # "tax" or "spending"
    entity: Optional[str] = None
    obr_line: Optional[str] = None
    payer: Optional[str] = None
    sign: Optional[str] = None
    zero_at_baseline: bool = False
    caseload: bool = False
    reads: tuple = ()
    notes: tuple = ()


@dataclass(frozen=True)
class DoubleCount:
    variable: str
    contained_in: str
    totals: tuple
    issue: str = ""


@dataclass(frozen=True)
class Exclusion:
    variable: str
    kind: str = ""
    head: str = ""
    spans: tuple = ()
    note: str = ""


@dataclass(frozen=True)
class Partition:
    schema_version: int
    totals: Mapping[str, TotalSpec]
    tax_heads: tuple
    spending_heads: tuple
    double_counts: tuple
    exclusions: tuple
    overlap_guards: tuple = ()
    source: str = "<memory>"
    sha256: str = ""
    raw: Mapping = field(default_factory=dict, compare=False, repr=False)

    @property
    def heads(self) -> tuple:
        return self.tax_heads + self.spending_heads

    def dropped(self, total: str, active: Iterable[str] = ()) -> set:
        """Variables the total leaves out while the given parameters are true."""
        active = set(active)
        spec = self.totals.get(total)
        if spec is None:
            return set()
        return {
            v
            for parameter, variables in spec.dropped_when
            if parameter in active
            for v in variables
        }

    def heads_in(self, total: str, active: Iterable[str] = ()) -> list:
        dropped = self.dropped(total, active)
        return [
            h for h in self.heads if total in h.totals and h.variable not in dropped
        ]

    def double_counts_in(self, total: str, active: Iterable[str] = ()) -> list:
        dropped = self.dropped(total, active)
        return [
            d
            for d in self.double_counts
            if total in d.totals and d.variable not in dropped
        ]

    def components(self, total: str, active: Iterable[str] = ()) -> list:
        """The variables the model should add for ``total``, per the partition."""
        return [h.variable for h in self.heads_in(total, active)] + [
            d.variable for d in self.double_counts_in(total, active)
        ]

    def component_variables(self) -> list:
        """Every variable named as a head or a declared double count, once."""
        return list(
            dict.fromkeys(
                [h.variable for h in self.heads]
                + [d.variable for d in self.double_counts]
            )
        )

    def head_by_variable(self, variable: str) -> Optional[Head]:
        for head in self.heads:
            if head.variable == variable:
                return head
        return None

    def is_tax_total(self, total: str) -> bool:
        spec = self.totals.get(total)
        return spec is not None and spec.kind == "tax"

    def dropped_when_parameters(self) -> list:
        return list(
            dict.fromkeys(
                p for spec in self.totals.values() for p, _ in spec.dropped_when
            )
        )

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "sha256": self.sha256,
            "schema_version": self.schema_version,
            "tax_heads": [_head_dict(h) for h in self.tax_heads],
            "spending_heads": [_head_dict(h) for h in self.spending_heads],
            "model_double_counts": [
                {
                    "variable": d.variable,
                    "contained_in": d.contained_in,
                    "totals": list(d.totals),
                    "issue": d.issue,
                }
                for d in self.double_counts
            ],
            "totals": {
                name: {
                    "kind": t.kind,
                    "module": t.module,
                    "list": t.list_name,
                    "dropped_when": {p: list(v) for p, v in t.dropped_when},
                }
                for name, t in self.totals.items()
            },
        }


def _head_dict(head: Head) -> dict:
    return {
        "id": head.id,
        "label": head.label,
        "variable": head.variable,
        "totals": list(head.totals),
        "report_group": head.report_group,
        "kind": head.kind,
        "entity": head.entity,
        "obr_line": head.obr_line,
        "payer": head.payer,
        "sign": head.sign,
        "zero_at_baseline": head.zero_at_baseline,
        "caseload": head.caseload,
        "notes": list(head.notes),
    }


def group_label(report_group: str) -> str:
    """``excise_duties`` -> ``Excise duties``; labels already in prose pass through."""
    text = report_group.replace("_", " ").strip()
    return text[:1].upper() + text[1:] if text else "Other"


def default_partition_path() -> Optional[Path]:
    """The partition shipped with the installed ``policyengine_uk``, if any."""
    spec = importlib.util.find_spec("policyengine_uk")
    if spec is None or not spec.submodule_search_locations:
        return None
    for location in spec.submodule_search_locations:
        candidate = Path(location) / PARTITION_RELATIVE_PATH
        if candidate.exists():
            return candidate
    return None


def _as_tuple(value, field_name: str, where: str) -> tuple:
    if value is None:
        return ()
    if isinstance(value, str):
        raise PartitionError(f"{where}: {field_name} must be a list, not a string")
    return tuple(str(v) for v in value)


def _parse_total(name: str, raw: Mapping) -> TotalSpec:
    if raw is None:
        raw = {}
    if not isinstance(raw, Mapping):
        raise PartitionError(f"totals.{name} must be a mapping")
    known = KNOWN_TOTALS.get(name)
    kind = raw.get("kind") or (known[0] if known else None)
    module = raw.get("module") or (known[1] if known else None)
    list_name = raw.get("list") or (known[2] if known else None)
    if kind not in ("tax", "spending") or not module or not list_name:
        raise PartitionError(
            f"totals.{name}: an unfamiliar total needs kind (tax or spending), module and list"
        )
    dropped = []
    for parameter, variables in (raw.get("dropped_when") or {}).items():
        dropped.append(
            (str(parameter), _as_tuple(variables, "dropped_when", f"totals.{name}"))
        )
    return TotalSpec(
        name=name,
        kind=kind,
        module=str(module),
        list_name=str(list_name),
        label=str(raw.get("label") or ""),
        dropped_when=tuple(dropped),
    )


def _parse_head(raw: Mapping, kind: str, index: int) -> Head:
    where = f"{kind}_heads[{index}]"
    if not isinstance(raw, Mapping):
        raise PartitionError(f"{where}: must be a mapping")
    missing = [k for k in ("id", "label", "variable", "totals") if not raw.get(k)]
    if missing:
        raise PartitionError(f"{where}: missing {missing}")
    zero = raw.get("zero_at_baseline")
    if zero not in (None, "expected"):
        raise PartitionError(f"{where}: zero_at_baseline must be 'expected' or absent")
    notes = tuple(
        f"{key.replace('_', ' ')}: {' '.join(str(raw[key]).split())}"
        for key in ("obr_line_note", "zero_at_baseline_note", "data_note", "model_note")
        if raw.get(key)
    )
    reads = tuple(
        str(r.get("head")) for r in (raw.get("reads") or []) if isinstance(r, Mapping)
    )
    caseload = raw.get("caseload")
    return Head(
        id=str(raw["id"]),
        label=str(raw["label"]),
        variable=str(raw["variable"]),
        totals=_as_tuple(raw.get("totals"), "totals", where),
        report_group=str(raw.get("report_group") or "other"),
        kind=kind,
        entity=raw.get("entity"),
        obr_line=raw.get("obr_line"),
        payer=raw.get("payer"),
        sign=raw.get("sign"),
        zero_at_baseline=zero == "expected",
        caseload=bool(caseload) if caseload is not None else kind == "spending",
        reads=reads,
        notes=notes,
    )


def parse_partition(
    raw: Mapping, source: str = "<memory>", sha256: str = ""
) -> Partition:
    """Build a partition from parsed YAML, raising on any inconsistency."""
    if not isinstance(raw, Mapping):
        raise PartitionError(f"{source}: the partition must be a mapping")
    version = raw.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise PartitionError(
            f"{source}: schema_version {version!r} is not one of "
            f"{sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )
    totals = {
        str(name): _parse_total(str(name), spec)
        for name, spec in (raw.get("totals") or {}).items()
    }
    tax_heads = tuple(
        _parse_head(h, "tax", i) for i, h in enumerate(raw.get("tax_heads") or [])
    )
    spending_heads = tuple(
        _parse_head(h, "spending", i)
        for i, h in enumerate(raw.get("spending_heads") or [])
    )
    double_counts = []
    for i, dc in enumerate(raw.get("model_double_counts") or []):
        where = f"model_double_counts[{i}]"
        if (
            not isinstance(dc, Mapping)
            or not dc.get("variable")
            or not dc.get("contained_in")
        ):
            raise PartitionError(f"{source}: {where} needs variable and contained_in")
        double_counts.append(
            DoubleCount(
                variable=str(dc["variable"]),
                contained_in=str(dc["contained_in"]),
                totals=_as_tuple(dc.get("totals"), "totals", where),
                issue=str(dc.get("issue") or ""),
            )
        )
    exclusions = tuple(
        Exclusion(
            variable=str(e.get("variable")),
            kind=str(e.get("kind") or ""),
            head=str(e.get("head") or ""),
            spans=_as_tuple(e.get("spans"), "spans", "exclusions"),
            note=str(e.get("note") or e.get("reason") or ""),
        )
        for e in (raw.get("exclusions") or [])
        if isinstance(e, Mapping)
    )
    partition = Partition(
        schema_version=version,
        totals=totals,
        tax_heads=tax_heads,
        spending_heads=spending_heads,
        double_counts=tuple(double_counts),
        exclusions=exclusions,
        overlap_guards=tuple(raw.get("overlap_guards") or ()),
        source=source,
        sha256=sha256,
        raw=raw,
    )
    problems = structural_problems(partition)
    if problems:
        raise PartitionError(f"{source}:\n- " + "\n- ".join(problems))
    return partition


def load_partition(path) -> Partition:
    path = Path(path)
    data = path.read_bytes()
    return parse_partition(
        yaml.safe_load(data), source=str(path), sha256=hashlib.sha256(data).hexdigest()
    )


def structural_problems(partition: Partition) -> list:
    """Inconsistencies visible from the partition alone, without the model."""
    problems = []
    heads = partition.heads
    head_ids = {h.id for h in heads}
    for name, count in Counter(h.id for h in heads).items():
        if count > 1:
            problems.append(f"head id {name!r} is used {count} times")
    for name, count in Counter(h.variable for h in heads).items():
        if count > 1:
            problems.append(f"variable {name!r} is the variable of {count} heads")
    head_variables = {h.variable for h in heads}
    for head in heads:
        if len(set(head.totals)) != len(head.totals):
            problems.append(f"head {head.id!r} lists a total twice")
        for total in head.totals:
            spec = partition.totals.get(total)
            if spec is None:
                problems.append(f"head {head.id!r} names unknown total {total!r}")
            elif spec.kind != head.kind:
                problems.append(
                    f"{head.kind} head {head.id!r} is in {total!r}, a {spec.kind} total"
                )
        if head.entity is not None and head.entity not in ENTITIES:
            problems.append(f"head {head.id!r} has unknown entity {head.entity!r}")
        if head.sign not in SIGNS:
            problems.append(f"head {head.id!r} has unknown sign {head.sign!r}")
        for read in head.reads:
            if read not in head_ids:
                problems.append(
                    f"head {head.id!r} declares a read of unknown head {read!r}"
                )
    for name, spec in partition.totals.items():
        listed = set(partition.components(name))
        for parameter, variables in spec.dropped_when:
            for variable in variables:
                if variable not in listed:
                    problems.append(
                        f"totals.{name} drops {variable!r} under {parameter}, but no head "
                        "or double count of that total is that variable"
                    )
    for dc in partition.double_counts:
        if dc.variable in head_variables:
            problems.append(
                f"double count {dc.variable!r} is also a head; it would be counted twice"
            )
        container = partition.head_by_variable(dc.contained_in)
        if container is None:
            problems.append(
                f"double count {dc.variable!r} is contained in {dc.contained_in!r}, "
                "which is not a head variable"
            )
        else:
            missing = [t for t in dc.totals if t not in container.totals]
            if missing:
                problems.append(
                    f"double count {dc.variable!r} is in {missing}, which its "
                    f"container {dc.contained_in!r} is not"
                )
        for total in dc.totals:
            if total not in partition.totals:
                problems.append(
                    f"double count {dc.variable!r} names unknown total {total!r}"
                )
    for name, count in Counter(d.variable for d in partition.double_counts).items():
        if count > 1:
            problems.append(f"double count {name!r} is declared {count} times")
    for exclusion in partition.exclusions:
        if exclusion.variable in head_variables:
            problems.append(
                f"excluded variable {exclusion.variable!r} is also a head variable"
            )
        for referenced in ([exclusion.head] if exclusion.head else []) + list(
            exclusion.spans
        ):
            if referenced not in head_ids:
                problems.append(
                    f"exclusion {exclusion.variable!r} refers to unknown head {referenced!r}"
                )
    return problems


def read_model_lists(partition: Partition) -> tuple:
    """Import each total's component list from the model.

    Returns ``(lists, problems)``: the lists that could be read, keyed by
    total, and a description of every total whose list could not be read.
    """
    lists, problems = {}, []
    for name, spec in partition.totals.items():
        try:
            module = importlib.import_module(spec.module)
            values = getattr(module, spec.list_name)
        except (ImportError, AttributeError) as error:
            problems.append(
                f"{name}: cannot read {spec.module}.{spec.list_name}: {error}"
            )
            continue
        lists[name] = [str(v) for v in values]
    return lists, problems


def closure_problems(
    partition: Partition,
    model_lists: Mapping[str, Iterable[str]],
    model_variables: Optional[Mapping] = None,
) -> list:
    """Differences between the partition and the model's own component lists.

    For every total, the heads and double counts naming it must be exactly
    the model's list, each listed once; every named variable must exist, and
    a head's declared entity must be its variable's entity.
    """
    problems = []
    for total, listed in model_lists.items():
        listed = list(listed)
        for variable, count in Counter(listed).items():
            if count > 1:
                problems.append(f"{total}: the model lists {variable!r} {count} times")
        expected, assigned = set(listed), set(partition.components(total))
        for variable in sorted(expected - assigned):
            problems.append(
                f"{total}: the model adds {variable!r}, which no head or declared "
                "double count covers"
            )
        for variable in sorted(assigned - expected):
            problems.append(
                f"{total}: the partition puts {variable!r} in this total, but the "
                "model does not add it"
            )
    if model_variables is not None:
        named = partition.component_variables() + [
            d.contained_in for d in partition.double_counts
        ]
        for variable in sorted(set(named) - set(model_variables)):
            problems.append(f"{variable!r} is not a model variable")
        for head in partition.heads:
            definition = (
                model_variables.get(head.variable)
                if hasattr(model_variables, "get")
                else None
            )
            if (
                head.entity
                and definition is not None
                and definition.entity.key != head.entity
            ):
                problems.append(
                    f"head {head.id!r} says entity {head.entity!r}, but {head.variable} "
                    f"is a {definition.entity.key} variable"
                )
    return problems
