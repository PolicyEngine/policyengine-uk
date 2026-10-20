"""The report specification: horizon, measures and flag thresholds."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

import yaml

DEFAULT_SPEC_PATH = Path(__file__).with_name("report_spec.yaml")


class SpecError(ValueError):
    pass


@dataclass(frozen=True)
class Threshold:
    absolute: float
    relative: float = 0.0

    def limit(self, base: float) -> float:
        return max(self.absolute, self.relative * abs(base))

    def exceeded(self, base: float, head: float) -> bool:
        return abs(head - base) > self.limit(base)


@dataclass(frozen=True)
class Spec:
    raw: Mapping
    first_year: int
    last_year: int
    guard_year: int
    poverty_measures: tuple
    poverty_groups: tuple
    inequality: tuple
    decile_variable: str
    income_variable: str
    flags: Mapping[str, Threshold]
    identity_relative_tolerance: float
    identity_absolute_tolerance: float
    counted_once_tolerance: float
    max_comment_characters: int

    @property
    def years(self) -> list:
        return list(range(self.first_year, self.last_year + 1))

    def threshold(self, kind: str) -> Optional[Threshold]:
        return self.flags.get(kind)


def fiscal_year_label(year: int) -> str:
    return f"{year}-{(year + 1) % 100:02d}"


def parse_spec(raw: Mapping) -> Spec:
    if raw.get("schema_version") != 1:
        raise SpecError(
            f"unsupported spec schema_version {raw.get('schema_version')!r}"
        )
    horizon = raw.get("horizon") or {}
    first, last = int(horizon["first_year"]), int(horizon["last_year"])
    if last < first:
        raise SpecError("horizon.last_year is before horizon.first_year")
    guard_year = int(raw.get("guard_year", first))
    poverty = raw.get("poverty") or {}
    flags = {
        kind: Threshold(float(v.get("absolute", 0.0)), float(v.get("relative", 0.0)))
        for kind, v in (raw.get("flags") or {}).items()
    }
    deciles = raw.get("deciles") or {}
    return Spec(
        raw=raw,
        first_year=first,
        last_year=last,
        guard_year=guard_year,
        poverty_measures=tuple(poverty.get("measures") or ()),
        poverty_groups=tuple(poverty.get("groups") or ()),
        inequality=tuple(raw.get("inequality") or ()),
        decile_variable=str(deciles.get("decile_variable", "household_income_decile")),
        income_variable=str(deciles.get("income_variable", "household_net_income")),
        flags=flags,
        identity_relative_tolerance=float(raw.get("identity_relative_tolerance", 1e-6)),
        identity_absolute_tolerance=float(
            raw.get("identity_absolute_tolerance_gbp", 1e6)
        ),
        counted_once_tolerance=float(raw.get("counted_once_tolerance", 1e-3)),
        max_comment_characters=int(
            (raw.get("comment") or {}).get("max_characters", 60000)
        ),
    )


def load_spec(path=None, years: Optional[str] = None) -> Spec:
    """Load the spec, optionally overriding the horizon with ``"2025-2031"``."""
    with open(path or DEFAULT_SPEC_PATH) as f:
        raw = yaml.safe_load(f)
    if years:
        start, _, end = years.partition("-")
        raw = dict(raw)
        raw["horizon"] = {"first_year": int(start), "last_year": int(end or start)}
    return parse_spec(raw)
