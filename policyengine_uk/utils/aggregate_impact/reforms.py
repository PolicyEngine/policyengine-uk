"""The standard reform set: loading, building reforms, and responsiveness."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Sequence

import yaml

from .spec import fiscal_year_label

DEFAULT_REFORMS_PATH = Path(__file__).with_name("standard_reforms.yaml")
_INDEXED = re.compile(r"^(?P<name>[^\[\]]+)\[(?P<index>\d+)\]$")


class ReformSpecError(ValueError):
    pass


@dataclass(frozen=True)
class Responds:
    """What a reform must do to the weighted total of one model variable."""

    variable: str
    direction: str  # "up" or "down"
    minimum: float


@dataclass(frozen=True)
class StandardReform:
    id: str
    name: str
    parameters: Mapping = field(default_factory=dict)
    scale: Mapping = field(default_factory=dict)
    responds: Optional[Responds] = None


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def parse_reforms(raw: Mapping) -> list:
    """Parse a reform file.

    Accepts the standard schema and the reform-cost fixture schema (a
    ``reforms`` list of ``name`` and ``parameters``, with no ``responds``).
    """
    reforms, seen = [], set()
    for index, entry in enumerate((raw or {}).get("reforms") or []):
        where = f"reforms[{index}]"
        if not isinstance(entry, Mapping) or not entry.get("name"):
            raise ReformSpecError(f"{where}: needs a name")
        parameters = dict(entry.get("parameters") or {})
        scale = {str(k): float(v) for k, v in (entry.get("scale") or {}).items()}
        if not parameters and not scale:
            raise ReformSpecError(f"{where}: needs parameters or scale")
        for path, factor in scale.items():
            if not factor > 0:
                raise ReformSpecError(
                    f"{where}: scale factor for {path} must be positive"
                )
        responds = None
        if entry.get("responds"):
            r = entry["responds"]
            if r.get("direction") not in ("up", "down"):
                raise ReformSpecError(f"{where}: responds.direction must be up or down")
            minimum = float(r.get("minimum", 0))
            if not r.get("variable") or not minimum > 0:
                raise ReformSpecError(
                    f"{where}: responds needs a variable and a positive minimum"
                )
            responds = Responds(str(r["variable"]), r["direction"], minimum)
        reform_id = str(entry.get("id") or _slug(str(entry["name"])))
        if reform_id in seen:
            raise ReformSpecError(f"{where}: reform id {reform_id!r} is used twice")
        seen.add(reform_id)
        reforms.append(
            StandardReform(reform_id, str(entry["name"]), parameters, scale, responds)
        )
    return reforms


def load_reforms(path=None) -> list:
    with open(path or DEFAULT_REFORMS_PATH) as f:
        return parse_reforms(yaml.safe_load(f))


def parameter_node(root, path: str):
    """Navigate ``a.b[0].c`` from a parameter tree's root."""
    node = root
    for part in path.split("."):
        indexed = _INDEXED.match(part)
        if indexed:
            node = getattr(node, indexed["name"]).brackets[int(indexed["index"])]
        else:
            node = getattr(node, part)
    return node


# Parameter metadata under which a bare year does not mean model year Y on the
# reform-dict route (it means the fiscal year from 6 April), or under which the
# value read at 1 January Y is not the value the model uses for Y.
CALENDAR_DATED_METADATA = ("preserve_calendar_dates", "fiscal_year_blend")


def reform_parameters(
    reform: StandardReform, baseline_parameters, years: Sequence[int]
) -> dict:
    """The parameter-change dict for ``Microsimulation(reform=...)``.

    A scaled parameter gets one bare-year entry per horizon year: the
    baseline's value for that model year times the factor. On the
    reform-dict route a bare year sets model year Y alone, and the processed
    baseline's value at 1 January Y is the value the model uses for Y
    (``convert_to_fiscal_year_parameters`` writes the fiscal year's value
    over the calendar year). Neither holds for a parameter that keeps its
    calendar dates or blends fiscal years, so scaling one is refused.
    """
    changes = dict(reform.parameters)
    for path, factor in reform.scale.items():
        node = parameter_node(baseline_parameters, path)
        metadata = getattr(node, "metadata", None) or {}
        dated = [key for key in CALENDAR_DATED_METADATA if metadata.get(key)]
        if dated:
            raise ReformSpecError(
                f"{reform.id}: cannot scale {path}, which has {', '.join(dated)}; "
                "write its values with explicit dates instead"
            )
        changes[path] = {
            str(year): float(node(f"{year}-01-01")) * factor for year in years
        }
    return changes


def responsiveness(responds: Responds, changes: Mapping[int, float]) -> tuple:
    """Whether a reform moved its target enough, the right way, in every year.

    ``changes`` maps year to the reformed total minus the baseline total.
    Returns ``(ok, detail)``; ``detail`` names the failing years.
    """
    sign = 1.0 if responds.direction == "up" else -1.0
    failing = []
    for year, change in sorted(changes.items()):
        moved = sign * change
        if not moved >= responds.minimum:
            if change == 0:
                what = "did not move"
            elif moved < 0:
                what = f"moved the wrong way (£{change:,.0f})"
            else:
                what = f"moved only £{change:,.0f}"
            failing.append(
                f"{fiscal_year_label(int(year))}: {responds.variable} {what}"
            )
    if not changes:
        failing.append("no year was measured")
    detail = ""
    if failing:
        detail = (
            f"expected {responds.variable} {responds.direction} by at least "
            f"£{responds.minimum:,.0f} a year; " + "; ".join(failing)
        )
    return not failing, detail
