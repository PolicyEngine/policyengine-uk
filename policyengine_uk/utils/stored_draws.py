"""Draws a dataset build stores, and the one check that decides what a read of
one may return.

A stored draw is a uniform in [0, 1) that the producer of a dataset assigns
to each unit and stores; the model compares it with a rate it owns. The
registry below records each draw's entity, value type and definition period.
A simulation built from data reads a registered draw only through
``Simulation.calculate``, which asks ``input_source`` which input
policyengine-core will read before core computes the answer, and checks
core's answer against that input afterwards (``check_draw_answer``).

``input_source`` changes nothing in storage and returns no array. It returns
the period, branch, storage tier and sequence number of the supplied input
core will read for the request, None where no supplied input reaches the
period, and raises otherwise. Metadata alone decides whether a value is
supplied (see ``policyengine_uk.utils.supplied_inputs``). Arrays are compared
only to accept a derived value core cached in the slot it reads: it must
equal its supplied source, or, with no supplied source, the holder's default.

The check reads policyengine-core's private members: ``Holder._branch_storing``,
``Holder._memory_storage``, ``Holder._disk_storage``,
``Holder._stored_sequence_number`` and core's carry-over order
``_latest_input_key``. Tests pin the behaviour it relies on for each
qualified core version (see ``QUALIFIED_CORE_VERSIONS``).
"""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import NamedTuple, Optional

import numpy as np
from policyengine_core import periods
from policyengine_core.periods import Period
from policyengine_core.simulations.simulation import _latest_input_key

from policyengine_uk.utils.supplied_inputs import (
    SUPPLIED_INPUT_VARIABLES,
    _counted_input,
)

# The policyengine-core versions whose provenance, dispatch, lifecycle and
# loading behaviour the tests qualify. tests/code_health/test_core_version_gate.py
# fails when uv.lock or the installed core holds any other.
QUALIFIED_CORE_VERSIONS = frozenset({"3.33.3", "3.34.1"})

# policyengine-core splits on-disk storage keys at every underscore, so a
# branch name with one breaks its enumeration of inputs on disk.
CORE_DISK_KEY_ISSUE = "PolicyEngine/policyengine-core#526"


class DrawSchema(NamedTuple):
    """What a registered draw's definition must keep."""

    entity: str
    value_type: type
    definition_period: str


REGISTERED_DRAWS = {
    "uc_new_claimant_health_element_draw": DrawSchema("benunit", float, periods.YEAR),
    "pip_phase_in_draw": DrawSchema("person", float, periods.YEAR),
}
# Simulation.calculate tests each variable name against this set, once.
REGISTERED_DRAW_NAMES = frozenset(REGISTERED_DRAWS)
assert REGISTERED_DRAW_NAMES <= SUPPLIED_INPUT_VARIABLES


class InputSource(NamedTuple):
    """The supplied input policyengine-core reads for a request."""

    period: Period
    branch_name: str
    tier: str
    sequence_number: Optional[int]


class StoredDrawError(ValueError):
    """A read or write of a registered draw that the model refuses."""


# How many pe-uk calculations (calculate, calculate_add, calculate_divide,
# calculate_output) are running in this context, on any simulation.
_calculation_depth: ContextVar[int] = ContextVar(
    "policyengine_uk_calculation_depth", default=0
)


@contextmanager
def calculation():
    """Count a pe-uk calculation as running while the block runs."""
    token = _calculation_depth.set(_calculation_depth.get() + 1)
    try:
        yield
    finally:
        _calculation_depth.reset(token)


def calculation_in_flight() -> bool:
    return _calculation_depth.get() > 0


def _describe(name: str, period, branch_name: Optional[str], tier=None) -> str:
    where = f"{name} for {period}"
    if branch_name is not None:
        where += f" on branch {branch_name!r}"
    if tier is not None:
        where += f" ({tier})"
    return where


def _check_schema(variable, name: str, schema: DrawSchema, which: str) -> None:
    if variable is None:
        raise StoredDrawError(f"{name} has no {which}.")
    kept = (
        variable.entity.key == schema.entity
        and variable.value_type is schema.value_type
        and variable.definition_period == schema.definition_period
    )
    if not kept:
        raise StoredDrawError(
            f"The {which} of {name} has entity {variable.entity.key!r}, type "
            f"{variable.value_type.__name__} and period "
            f"{variable.definition_period!r}; a stored draw needs entity "
            f"{schema.entity!r}, type {schema.value_type.__name__} and period "
            f"{schema.definition_period!r}."
        )
    computed = [
        attribute
        for attribute, value in (
            ("a formula", len(variable.formulas) > 0),
            ("uprating", variable.uprating is not None),
            ("defined_for", variable.defined_for is not None),
            ("calculate_output", variable.calculate_output is not None),
            ("adds", bool(variable.adds)),
            ("subtracts", bool(variable.subtracts)),
            (
                "requires_computation_after",
                variable.requires_computation_after is not None,
            ),
        )
        if value
    ]
    if computed:
        raise StoredDrawError(
            f"The {which} of {name} has {', '.join(computed)}; a stored draw "
            "is an input the dataset supplies, read as stored."
        )


def _check_request(holder, name: str, schema: DrawSchema, period: Period) -> None:
    if (
        period.unit != schema.definition_period
        or period.size != 1
        or holder._storage_period(period) != period
    ):
        raise StoredDrawError(
            f"{name} is read only for one {schema.definition_period}, as "
            f"stored; {period} is not one. A draw is a share of nothing, so "
            "it has no sum over months or twelfth."
        )


def _check_definition(simulation, holder, name, schema, period) -> None:
    system = simulation.tax_benefit_system
    current = system.variables.get(name)
    _check_schema(current, name, schema, "current definition")
    _check_schema(holder.variable, name, schema, "holder's definition")
    if current.is_neutralized or holder.variable.is_neutralized:
        raise StoredDrawError(
            f"{name} is neutralised, so policyengine-core would return its "
            "default instead of the stored draw."
        )
    try:
        abolished = bool(system.parameters(period).gov.abolitions[name])
    except Exception:
        # Core reads the same switch and ignores its absence.
        abolished = False
    if abolished:
        raise StoredDrawError(
            f"gov.abolitions abolishes {name} in {period}, so "
            "policyengine-core would return its default instead of the "
            "stored draw."
        )
    if getattr(simulation, "macro_cache_read", False):
        raise StoredDrawError(
            f"The simulation reads policyengine-core's macro cache, which "
            f"could answer {name} from a file instead of the stored draw."
        )


def _sequence_number(holder, period: Period, branch_name: str):
    return holder._stored_sequence_number(period, branch_name)


def _supplied_source(simulation, holder, name, period, branch_name):
    """``InputSource`` for the input stored for ``period`` on ``branch_name``
    if it counts as supplied there, else None."""
    if _counted_input(simulation, holder, (name, branch_name, period)) is None:
        return None
    return InputSource(
        period, branch_name, "memory", _sequence_number(holder, period, branch_name)
    )


def _carry_source(simulation, holder, name, schema, period) -> Optional[InputSource]:
    """The input core's carry-over would read for ``period``: of the periods
    ``Holder.get_input_periods`` lists that start no later than it, the one
    ``_latest_input_key`` ranks last. It must be supplied."""
    branch_name = simulation.branch_name
    candidates = [
        input_period
        for input_period in holder.get_input_periods(branch_name)
        if input_period.start <= period.start
    ]
    if not candidates:
        return None
    source_period = max(
        candidates,
        key=lambda candidate: _latest_input_key(candidate, schema.definition_period),
    )
    source_branch = holder._branch_storing(source_period, branch_name)
    source = _supplied_source(simulation, holder, name, source_period, source_branch)
    if source is None:
        raise StoredDrawError(
            f"policyengine-core would carry "
            f"{_describe(name, source_period, source_branch, 'memory')} into "
            f"{period}, and that value is not a supplied input."
        )
    return source


def _source_array(holder, source: InputSource) -> np.ndarray:
    stored = holder._memory_storage.get(source.period, source.branch_name)
    return np.asarray(stored).astype(holder.variable.dtype)


def _same_array(first, second) -> bool:
    first = np.asarray(first)
    second = np.asarray(second)
    return (
        first.dtype == second.dtype
        and first.shape == second.shape
        and bool(np.array_equal(first, second))
    )


def input_source(population, name: str, period) -> Optional[InputSource]:
    """The supplied input policyengine-core reads for ``name`` at ``period``
    in ``population``'s simulation, or None where no supplied input reaches
    the period. Raises ``StoredDrawError`` where core would read anything
    else, naming the variable, period, branch and tier.

    Changes nothing in storage and returns no array.
    """
    schema = REGISTERED_DRAWS.get(name)
    if schema is None:
        raise StoredDrawError(f"{name} is not a registered stored draw.")
    simulation = population.simulation
    holder = population.get_holder(name)
    period = periods.period(period)
    _check_request(holder, name, schema, period)
    _check_definition(simulation, holder, name, schema, period)
    branch_name = simulation.branch_name
    if holder._disk_storage is not None:
        raise StoredDrawError(
            f"The holder of {name} keeps values on disk, where "
            f"policyengine-core cannot list inputs stored under a branch name "
            f"with an underscore ({CORE_DISK_KEY_ISSUE}). Read {name} from a "
            "simulation without memory_config."
        )
    storing = holder._branch_storing(period, branch_name)
    if storing is not None:
        memory = holder._memory_storage
        if not memory.is_derived(period, storing):
            source = _supplied_source(simulation, holder, name, period, storing)
            if source is None:
                raise StoredDrawError(
                    f"policyengine-core would read "
                    f"{_describe(name, period, storing, 'memory')}, a value "
                    "set as an input that is not a supplied one."
                )
            return source
        cached = memory.get(period, storing)
        source = _carry_source(simulation, holder, name, schema, period)
        if source is not None:
            if _same_array(cached, _source_array(holder, source)):
                return source
            raise StoredDrawError(
                f"policyengine-core would read the value cached for "
                f"{_describe(name, period, storing, 'memory')}, which differs "
                f"from its supplied source "
                f"{_describe(name, source.period, source.branch_name)}."
            )
        if _same_array(cached, holder.default_array()):
            return None
        raise StoredDrawError(
            f"policyengine-core would read the value cached for "
            f"{_describe(name, period, storing, 'memory')}, but no supplied "
            "input reaches the period and the value is not the default."
        )
    source = _carry_source(simulation, holder, name, schema, period)
    if source is None:
        return None
    if not simulation.tax_benefit_system.auto_carry_over_input_variables:
        raise StoredDrawError(
            f"The tax-benefit system does not carry inputs over, so "
            f"policyengine-core would return the default for {name} in "
            f"{period} instead of the input supplied for {source.period}."
        )
    return source


def check_draw_answer(simulation, name: str, period, source: InputSource, raw):
    """Raise unless ``raw``, core's answer for a read ``input_source`` traced
    to ``source``, is that source's array, cast to the holder's type, and the
    source is unchanged."""
    population = simulation.get_variable_population(name)
    period = periods.period(period)
    after = input_source(population, name, period)
    if after != source:
        raise StoredDrawError(
            f"The supplied source of {name} for {period} changed while "
            f"policyengine-core read it: {source} before, {after} after."
        )
    holder = population.get_holder(name)
    if not _same_array(raw, _source_array(holder, source)):
        raise StoredDrawError(
            f"policyengine-core returned a value for {name} in {period} on "
            f"branch {simulation.branch_name!r} that is not its supplied "
            f"source {_describe(name, source.period, source.branch_name, source.tier)}."
        )


def has_derived_values(holder) -> bool:
    """Whether ``holder`` stores any value the simulation calculated."""
    for storage in (holder._memory_storage, holder._disk_storage):
        if storage is None:
            continue
        for branch_name, stored_period in storage.get_known_branch_periods():
            if storage.is_derived(stored_period, branch_name):
                return True
    return False


def check_new_draw_input(simulation, name: str) -> None:
    """Refuse a new input for a registered draw while a calculation runs, or
    while the holder stores a value calculated from an earlier state."""
    if calculation_in_flight():
        raise StoredDrawError(
            f"{name} cannot be set while a calculation is running: a stored "
            "draw holds what the dataset supplies, and a calculation reads it."
        )
    holder = simulation.get_holder(name)
    if has_derived_values(holder):
        raise StoredDrawError(
            f"{name} cannot be set after the simulation has calculated a "
            "value from it. Set the draw before reading it, or build a new "
            "simulation."
        )


def check_option_request(simulation, name: str, method: str) -> None:
    """Refuse a sum, twelfth or output callback of a registered draw."""
    raise StoredDrawError(
        f"{name} is a stored draw, read only for its own period as stored, "
        f"so {method} refuses it."
    )


# Stored outcome: whether a person takes up a student loan as a new borrower.
STUDENT_LOAN_TAKE_UP = "would_claim_student_loan"


def check_boolean_input(name: str, values) -> None:
    """Raise unless every value is a boolean or the integer 0 or 1.

    policyengine-core skips its missing-value check for boolean variables and
    casts every input to the variable's type, so a missing value would load
    as True. Check the raw values first.
    """
    array = np.asarray(values, dtype=object if _is_extension(values) else None)
    flat = array.reshape(-1)
    if array.dtype == bool:
        return
    if array.dtype.kind in "iu":
        bad = ~np.isin(flat, (0, 1))
    else:
        bad = np.array(
            [
                not (
                    isinstance(value, (bool, np.bool_))
                    or (
                        isinstance(value, (int, np.integer))
                        and not isinstance(value, (bool, np.bool_))
                        and value in (0, 1)
                    )
                )
                for value in flat
            ],
            dtype=bool,
        )
    if bad.any():
        examples = ", ".join(repr(value) for value in flat[bad][:5])
        raise StoredDrawError(
            f"{name} takes booleans or the integers 0 and 1, with nothing "
            f"missing; {int(bad.sum())} value(s) are not ({examples})."
        )


def _is_extension(values) -> bool:
    """A pandas extension array (nullable boolean, say), whose missing
    values numpy would otherwise turn into something else."""
    dtype = getattr(values, "dtype", None)
    return dtype is not None and not isinstance(dtype, np.dtype)
