"""Explicit, bounded assumptions for projecting aggregate realised gains.

These describe the baseline gains base, not a response to a simulated reform.
One factor applies to every CGT input, preserving the supplied composition.
"""

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path

import yaml
from policyengine_core.parameters import Parameter, ParameterNode


CGT_INPUTS = (
    "capital_gains_before_response",
    "capital_gains_badr",
    "capital_gains_residential_property",
    "capital_gains_carried_interest",
)
CGT_DATASET_INPUTS = ("capital_gains", *CGT_INPUTS)
CGT_GROWTH_PATH = "gov.economic_assumptions.yoy_growth.capital_gains"
CGT_INDEX_PATH = "gov.economic_assumptions.indices.capital_gains"


def check_capital_gains_projection_parameter(path: str) -> None:
    """Reject reform assignments to either generated projection parameter."""
    if path in (CGT_GROWTH_PATH, CGT_INDEX_PATH):
        raise ValueError(
            f"{path} is a generated capital gains projection parameter and cannot "
            "be reformed directly. Pass capital_gains_projection=CapitalGainsProjection(...) "
            "to Simulation or Microsimulation to change the gains growth assumptions."
        )


class _CapitalGainsProjectionParameter(Parameter):
    """A derived series: its growth and index must change together."""

    def update(self, *args, **kwargs) -> None:
        check_capital_gains_projection_parameter(self.name)


def _fingerprint(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


@dataclass(frozen=True)
class CapitalGainsProjection:
    """Aggregate nominal gains growth by UK fiscal-year starting year.

    ``annual_growth[2025]`` means FY2025–26 relative to FY2024–25. Rates
    must cover every year after ``base_year`` through the final forecast.
    There is no extrapolation outside this span. Supplied gains must use
    the same measurement basis as the projection; the class cannot infer
    an observation period or tax-base definition from an H5 filename.
    """

    name: str
    base_year: int
    annual_growth: Mapping[int, float] | tuple[tuple[int, float], ...]
    source: str
    vintage: str
    assumptions: str

    def __post_init__(self) -> None:
        for field in ("name", "source", "vintage", "assumptions"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Capital gains projection requires {field}.")
        if type(self.base_year) is not int or not 1 <= self.base_year < 9999:
            raise ValueError("Capital gains projection base_year must be a valid year.")
        items = (
            self.annual_growth.items()
            if isinstance(self.annual_growth, Mapping)
            else self.annual_growth
        )
        rates = tuple(items)
        if not rates or any(type(year) is not int for year, _ in rates):
            raise ValueError(
                "Capital gains projection requires integer forecast years."
            )
        rates = tuple(sorted(rates))
        years = [year for year, _ in rates]
        if years[-1] >= 9999 or years != list(range(self.base_year + 1, years[-1] + 1)):
            raise ValueError(
                "Capital gains projection years must be contiguous after base_year."
            )
        if any(
            isinstance(rate, bool)
            or not isinstance(rate, (int, float))
            or not math.isfinite(rate)
            or rate <= -1
            for _, rate in rates
        ):
            raise ValueError(
                "Capital gains growth rates must be finite and greater than -1."
            )
        object.__setattr__(
            self, "annual_growth", tuple((year, float(rate)) for year, rate in rates)
        )

    @property
    def end_year(self) -> int:
        return self.annual_growth[-1][0]

    @property
    def metadata(self) -> dict:
        """Serializable source contract, excluding runtime population assumptions."""
        return {
            "name": self.name,
            "base_year": self.base_year,
            "end_year": self.end_year,
            "annual_aggregate_growth": dict(self.annual_growth),
            "source": self.source,
            "vintage": self.vintage,
            "assumptions": self.assumptions,
            "scope": "common factor for all CGT inputs, including signed net gains",
            "period": "UK fiscal year starting in the labelled year",
            "terminal_assumption": "none; projection outside the span raises",
        }

    @property
    def fingerprint(self) -> str:
        return _fingerprint(self.metadata)

    def validate_span(self, source_year: int, target_year: int) -> None:
        if not self.base_year <= source_year <= target_year <= self.end_year:
            raise ValueError(
                f"Capital gains projection {self.name!r} supports "
                f"{self.base_year}–{self.end_year}, not {source_year}–{target_year}. "
                "Supply inputs for the requested year or a projection covering this span."
            )


def obr_eot_projection() -> CapitalGainsProjection:
    """Experimental common-factor sensitivity, not an OBR all-gains forecast.

    The underlying November 2025 EOT costing determinant excludes carried
    interest and is not established as a pre-AEA, policy-free gains series.
    Applying it to other components holds composition fixed by assumption.
    """
    path = Path(__file__).with_name("capital_gains_projections") / "obr_eot.yaml"
    return CapitalGainsProjection(**yaml.safe_load(path.read_text()))


def add_capital_gains_projection(
    parameters: ParameterNode, projection: CapitalGainsProjection | None = None
) -> ParameterNode:
    """Install matching dataset growth and household indices on this tree."""
    economic = parameters.gov.economic_assumptions
    for parent_name in ("yoy_growth", "indices"):
        parent = getattr(economic, parent_name)
        existing = parent.children.get("capital_gains")
        if existing is not None and not isinstance(
            existing, _CapitalGainsProjectionParameter
        ):
            # A structural reform can replace a node without calling update().
            # Do not silently discard that attempted generated-path override.
            check_capital_gains_projection_parameter(
                f"gov.economic_assumptions.{parent_name}.capital_gains"
            )
    for parent_name in ("yoy_growth", "indices"):
        getattr(economic, parent_name).children.pop("capital_gains", None)
    if projection is None:
        # Copy both existing series exactly, including index rounding, so
        # introducing the dedicated paths does not change the legacy default.
        for parent_name in ("yoy_growth", "indices"):
            parent = getattr(economic, parent_name)
            original = parent.obr.per_capita.gdp
            parameter = _CapitalGainsProjectionParameter(
                f"gov.economic_assumptions.{parent_name}.capital_gains",
                data={
                    "values": {v.instant_str: v.value for v in original.values_list},
                    "metadata": {
                        **original.metadata,
                        "projection": {"name": "legacy_gdp_per_capita"},
                    },
                },
            )
            parent.add_child("capital_gains", parameter)
        return parameters

    population = economic.yoy_growth.ons.population
    growth = {}
    indices = {projection.base_year: 1.0}
    population_growth = {}
    for year, aggregate_rate in projection.annual_growth:
        population_rate = population(year)
        if (
            population_rate is None
            or not math.isfinite(population_rate)
            or population_rate <= -1
        ):
            raise ValueError(f"Invalid population growth for CGT projection in {year}.")
        population_growth[year] = population_rate
        growth[year] = (1 + aggregate_rate) / (1 + population_rate) - 1
        indices[year] = indices[year - 1] * (1 + growth[year])

    provenance = {
        **projection.metadata,
        "configuration_fingerprint": projection.fingerprint,
        "population_growth": population_growth,
        "annual_per_record_growth": growth,
        "per_record_index": indices,
    }
    provenance["fingerprint"] = _fingerprint(provenance)
    for parent_name, values in (("yoy_growth", growth), ("indices", indices)):
        parameter = _CapitalGainsProjectionParameter(
            f"gov.economic_assumptions.{parent_name}.capital_gains",
            data={
                "description": "Capital gains projection per record, net of population growth.",
                "values": {f"{year}-01-01": value for year, value in values.items()},
                "metadata": {
                    "unit": "/1",
                    "period": "year",
                    "label": "capital gains projection per record",
                    "preserve_calendar_dates": True,
                    "reference": [
                        {"title": projection.name, "href": projection.source}
                    ],
                    "projection": provenance,
                },
            },
        )
        getattr(economic, parent_name).add_child("capital_gains", parameter)
    return parameters
