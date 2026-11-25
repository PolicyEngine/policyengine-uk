"""Caller-owned, validated current-law baselines for local H5 inputs."""

from __future__ import annotations

import copy
from dataclasses import dataclass, fields, replace
import hashlib
from importlib import metadata, util
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from policyengine_uk.simulation import Simulation


@dataclass(frozen=True)
class _Identity:
    dataset_path: str
    dataset_sha256: str
    model_fingerprint: str
    model_version: str
    core_version: str
    core_fingerprint: str
    baseline_class: type
    capital_gains_projection: str | None
    trace: bool
    default_input_period: int
    default_calculation_period: int
    calendar_parameters: tuple[tuple[str, bool], ...] = ()


class PreparedBaseline:
    """Opaque result of ``Simulation.prepare_baseline``.

    The factory owns its current-law simulation. Consumers get independent
    clones; this object exposes no simulation or input-mutation interface.
    """

    __slots__ = ("_identity", "_simulation")

    def __new__(cls, *args, **kwargs):
        raise TypeError("Use Simulation.prepare_baseline to prepare a baseline.")


def _invalid(reason: str) -> ValueError:
    return ValueError(
        f"Cannot reuse prepared baseline: {reason}. "
        "Omit prepared_baseline to construct a fresh baseline."
    )


def _local_source(dataset) -> Path:
    if not isinstance(dataset, (str, os.PathLike)):
        raise _invalid("dataset must be an explicit local H5 path")
    source = os.fspath(dataset)
    if not isinstance(source, str) or "://" in source:
        raise _invalid("remote dataset sources are not supported")
    path = Path(source)
    if path.suffix.lower() != ".h5":
        raise _invalid("dataset must be an explicit local H5 path")
    try:
        path = path.resolve(strict=True)
    except OSError as error:
        raise _invalid("local H5 dataset does not exist") from error
    if not path.is_file():
        raise _invalid("dataset must be a local H5 file")
    return path


def _core_fingerprint() -> str:
    """Identify Core's code even in an editable same-version installation."""
    spec = util.find_spec("policyengine_core")
    if spec is None or not spec.origin:
        raise _invalid("Core code identity is unavailable")
    root = Path(spec.origin).parent
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if (
            not path.is_file()
            or "__pycache__" in relative.parts
            or relative.parts[:1] == ("tests",)
            or path.suffix == ".pyc"
        ):
            continue
        digest.update(relative.as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _calendar_parameters(names) -> tuple[tuple[str, bool], ...]:
    from policyengine_uk.tax_benefit_system import parameter_reads_calendar_years

    reads = parameter_reads_calendar_years()
    return tuple((name, bool(reads(name))) for name in names)


def _identity(dataset, trace, capital_gains_projection, baseline_class, names=()):
    # These existing digests cover file contents, not modification times or
    # only the subset of parameters used for uprating.
    from policyengine_uk.utils.aggregate_impact.dataset import sha256_file
    from policyengine_uk.utils.aggregate_impact.measure import model_fingerprint

    from policyengine_uk.data.capital_gains_projection import CapitalGainsProjection

    if type(trace) is not bool:
        raise _invalid("trace must be a boolean")
    if (
        capital_gains_projection is not None
        and type(capital_gains_projection) is not CapitalGainsProjection
    ):
        raise _invalid("capital_gains_projection must be a CapitalGainsProjection")
    path = _local_source(dataset)
    model = model_fingerprint()
    if model is None:
        raise _invalid("model code identity is unavailable")
    return _Identity(
        dataset_path=str(path),
        dataset_sha256=sha256_file(path),
        model_fingerprint=model,
        model_version=metadata.version("policyengine-uk"),
        core_version=metadata.version("policyengine-core"),
        core_fingerprint=_core_fingerprint(),
        baseline_class=baseline_class,
        capital_gains_projection=(
            None
            if capital_gains_projection is None
            else capital_gains_projection.fingerprint
        ),
        trace=trace,
        default_input_period=baseline_class.default_input_period,
        default_calculation_period=baseline_class.default_calculation_period,
        calendar_parameters=_calendar_parameters(names) if names else (),
    )


def _require_same(expected: _Identity, actual: _Identity) -> None:
    for field in fields(_Identity):
        if getattr(expected, field.name) != getattr(actual, field.name):
            raise _invalid(f"{field.name} does not match the prepared baseline")


def validate_prepared_baseline_request(
    prepared,
    *,
    dataset,
    situation,
    has_scenario,
    trace,
    capital_gains_projection,
    baseline_class,
) -> None:
    """Reject unsupported explicit requests before ordinary data loading."""
    if prepared is None:
        return
    if type(prepared) is not PreparedBaseline:
        raise _invalid("use the token produced by Simulation.prepare_baseline")
    if situation is not None:
        raise _invalid("situation inputs are not supported")
    if not has_scenario:
        raise _invalid("a scenario or reform is required")
    expected = prepared._identity
    names = tuple(name for name, _ in expected.calendar_parameters)
    _require_same(
        expected,
        _identity(dataset, trace, capital_gains_projection, baseline_class, names),
    )


def _require_canonical(simulation, baseline_class) -> None:
    if (
        type(simulation) is not baseline_class
        or simulation.branch_name != "default"
        or getattr(simulation, "parent_branch", None) is not None
    ):
        raise _invalid("the prepared simulation is not canonical current law")
    if (
        getattr(simulation, "_calculations_in_flight", 0)
        or getattr(simulation, "_construction_reform_state", None) is not None
        or getattr(simulation, "_external_input_change_pending", False)
        or getattr(simulation, "memory_config", None) is not None
        or getattr(simulation, "_data_storage_dir", None) is not None
    ):
        raise _invalid("the prepared simulation has unsupported pending or disk state")


def prepare_current_law_baseline(
    baseline_class, *, dataset, trace=False, capital_gains_projection=None
) -> PreparedBaseline:
    """Build and own one canonical baseline; never adopt a user simulation."""
    before = _identity(dataset, trace, capital_gains_projection, baseline_class)
    simulation = baseline_class(
        dataset=before.dataset_path,
        trace=trace,
        capital_gains_projection=capital_gains_projection,
    )
    after = _identity(dataset, trace, capital_gains_projection, baseline_class)
    _require_same(before, after)
    _require_canonical(simulation, baseline_class)
    inner = getattr(simulation, "baseline", None)
    if (
        inner is None
        or inner is simulation
        or getattr(inner, "baseline", None) is not None
    ):
        raise _invalid("the current-law baseline has unsupported ancestry")
    _require_canonical(inner, baseline_class)
    names = tuple(
        sorted(
            {
                node.name
                for node in simulation.tax_benefit_system.parameters.get_descendants()
            }
        )
    )
    prepared = object.__new__(PreparedBaseline)
    prepared._identity = replace(after, calendar_parameters=_calendar_parameters(names))
    prepared._simulation = simulation
    return prepared


def _detached_clone(source, *, trace, memo):
    clone = source.clone(clone_tax_benefit_system=True, trace=trace)
    # Core owns holder-array, input-key, invalidation and store-history
    # copying; UK clone additionally preserves its model-input and CGT/ISA
    # provenance records. Detach the extra containers that native clone
    # intentionally shares, only on this API's fresh clone.
    for name in (
        "dataset",
        "input_variables",
        "calculated_periods",
        "_savings_income_projection",
    ):
        if hasattr(source, name):
            setattr(clone, name, copy.deepcopy(getattr(source, name), memo))
    for name, population in clone.populations.items():
        original = source.populations[name]
        population.ids = copy.deepcopy(original.ids, memo)
        for attribute in (
            "_members_entity_id",
            "_members_role",
            "_members_position",
            "_ordered_members_map",
        ):
            if hasattr(original, attribute):
                # Roles are canonical entity objects. Copy the array index,
                # retaining those identities, rather than deep-copying roles.
                value = getattr(original, attribute)
                if id(value) not in memo:
                    memo[id(value)] = copy.copy(value)
                setattr(population, attribute, memo[id(value)])
        # Core clones the system's variables, while existing holders can
        # still point at the old variable object. Keep metadata edits local.
        for variable_name, holder in population._holders.items():
            holder.variable = clone.tax_benefit_system.get_variable(variable_name)
    return clone


def reuse_prepared_baseline(
    prepared, *, dataset, trace, capital_gains_projection, baseline_class
):
    """Validate again after modifiers, then return an independent baseline."""
    validate_prepared_baseline_request(
        prepared,
        dataset=dataset,
        situation=None,
        has_scenario=True,
        trace=trace,
        capital_gains_projection=capital_gains_projection,
        baseline_class=baseline_class,
    )
    source = prepared._simulation
    _require_canonical(source, baseline_class)
    inner = getattr(source, "baseline", None)
    if inner is None or inner is source or getattr(inner, "baseline", None) is not None:
        raise _invalid("the current-law baseline has unsupported ancestry")
    _require_canonical(inner, baseline_class)
    # Preserve aliases within this consumer while sharing nothing mutable
    # with the preparation or another consumer.
    memo = {}
    clone = _detached_clone(source, trace=trace, memo=memo)
    clone.baseline = _detached_clone(inner, trace=inner.trace, memo=memo)
    return clone
