"""Subsample a simulation built from a dataset.

``Simulation.subsample`` keeps a weighted random sample of households and
gives the sample weights with the same totals as before. policyengine-core's
``subsample`` cannot do this for a UK simulation:

- it rebuilds through ``Simulation.build_from_dataset()`` with no arguments,
  and the UK builder takes the dataset to load;
- given that dataset, the UK builder still cannot load what core rebuilds
  from: core's flat-file ``Dataset``, which ``Dataset.load_dataset`` does not
  read. The UK builder would also rebuild every year from the first one,
  projected forward, rather than keep each year's inputs;
- it reads each person's household and benefit unit back from the stored
  ``person_household_id`` and ``person_benunit_id`` inputs, which need not be
  exact: the UK model has stored them as 32-bit floats, which hold integers
  exactly only up to 2**24, so larger identifiers would merge households and
  benefit units (policyengine-uk#2267);
- it rebuilds a ``baseline`` branch, while a UK simulation's baseline is a
  simulation of its own.

So the functions here take the households, benefit units and people from the
simulation's populations, whose identifiers and memberships are exact, and
subsample the baseline and the dataset with the same draw.
"""

import hashlib
import operator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from policyengine_core.periods import Period, period as period_
from policyengine_core.tracers import SimpleTracer

from policyengine_uk.data.dataset_schema import (
    UKMultiYearDataset,
    UKSingleYearDataset,
)
from policyengine_uk.utils.supplied_inputs import supplied_input_arrays

if TYPE_CHECKING:
    from policyengine_uk.simulation import Simulation

# Variables that count how many units of the population a record stands for.
# A subsample rescales each one that is supplied as an input, so that its
# total over its own entity is unchanged.
WEIGHT_VARIABLES = frozenset(
    {
        "household_weight",
        "benunit_weight",
        "person_weight",
        "original_weight",
        "raw_person_weight",
    }
)

# policyengine-core seeds a subsample with the dataset's name by default. UK
# datasets have no name, so every UK subsample without a seed uses this one.
DEFAULT_SEED = "policyengine-uk"

UKDataset = Union[UKSingleYearDataset, UKMultiYearDataset]


def _random_state(seed) -> np.random.RandomState:
    """A generator for ``seed``, which may be a number or text.

    ``RandomState`` keeps the same stream in every NumPy version, so a seed
    chooses the same households wherever it runs. The digest gives the same
    number in every process, which the built-in ``hash`` does not.
    """
    digest = hashlib.sha256(str(seed).encode("utf-8")).digest()
    return np.random.RandomState(int.from_bytes(digest[:4], "big"))


def draw_household_counts(
    weights: np.ndarray, n: int, seed, quantize_weights: bool = True
) -> np.ndarray:
    """Draw ``n`` households with replacement and count each one's draws.

    Only households with a positive weight can be drawn. Each draw picks a
    household with probability proportional to its weight, or with equal
    probability when ``quantize_weights`` is false.

    Returns:
        The number of times each household was drawn; the counts sum to ``n``.
    """
    n = operator.index(n)
    if n < 1:
        raise ValueError(f"A subsample needs at least one household, not {n}.")
    weights = np.asarray(weights, dtype=float)
    eligible = np.flatnonzero(weights > 0)
    if eligible.size == 0:
        raise ValueError("No household has a positive weight to sample by.")
    if not np.isfinite(weights[eligible]).all():
        raise ValueError("Household weights must be finite to sample by them.")
    probabilities = (
        weights[eligible] / weights[eligible].sum() if quantize_weights else None
    )
    draws = _random_state(seed).choice(
        eligible.size, size=n, replace=True, p=probabilities
    )
    counts = np.zeros(weights.size, dtype=np.int64)
    counts[eligible] = np.bincount(draws, minlength=eligible.size)
    return counts


def rescale_weights(
    weights: np.ndarray, counts: np.ndarray, quantize_weights: bool = True
) -> np.ndarray:
    """Weights for the drawn records that keep the total of ``weights``.

    A drawn record's new weight is proportional to the number of times its
    household was drawn (``counts``), and also to its old weight when
    ``quantize_weights`` is false. A record that was not drawn gets zero.
    """
    weights = np.asarray(weights, dtype=float)
    total = weights.sum()
    if not np.isfinite(total):
        raise ValueError("the weights do not have a finite total")
    if total == 0:
        return np.zeros_like(weights)
    drawn = counts.astype(float) if quantize_weights else weights * counts
    drawn_total = drawn.sum()
    if drawn_total == 0:
        raise ValueError(
            "the sampled records have no weight. Use quantize_weights=True or "
            "a different sample"
        )
    return drawn * (total / drawn_total)


def _rescaled(name: str, period, weights, counts, quantize_weights) -> np.ndarray:
    try:
        return rescale_weights(weights, counts, quantize_weights)
    except ValueError as error:
        raise ValueError(
            f"Cannot preserve the total of {name} for {period}: {error}."
        ) from error


def _subsample_table(
    table: pd.DataFrame, counts: np.ndarray, period, quantize_weights: bool
) -> pd.DataFrame:
    """The rows of ``table`` drawn at least once, with their new weights."""
    kept = counts > 0
    subsample = table.loc[kept].reset_index(drop=True)
    for column in table.columns:
        if column in WEIGHT_VARIABLES:
            weights = _rescaled(
                column, period, table[column].values, counts, quantize_weights
            )
            subsample[column] = weights[kept]
    return subsample


def _subsample_single_year_dataset(
    dataset: UKSingleYearDataset,
    household_ids: np.ndarray,
    counts: np.ndarray,
    quantize_weights: bool,
) -> UKSingleYearDataset:
    # Read the stored tables, in which enum columns stay encoded; the public
    # properties decode every enum column of the whole table.
    person, benunit, household = dataset.tables
    draws = pd.Series(counts, index=household_ids)

    def draws_of(households) -> np.ndarray:
        return draws.reindex(np.asarray(households)).fillna(0).values

    # A benefit unit belongs to the household of its members.
    benunit_household = person.groupby("person_benunit_id")[
        "person_household_id"
    ].first()
    tables = [
        _subsample_table(table, table_counts, dataset.time_period, quantize_weights)
        for table, table_counts in (
            (person, draws_of(person["person_household_id"])),
            (
                benunit,
                draws_of(benunit_household.reindex(benunit["benunit_id"].values)),
            ),
            (household, draws_of(household["household_id"])),
        )
    ]
    subsample = UKSingleYearDataset(
        person=tables[0],
        benunit=tables[1],
        household=tables[2],
        fiscal_year=dataset.time_period,
    )
    subsample._enum_columns = dict(dataset._enum_columns)
    return subsample


def subsample_dataset(
    dataset: UKDataset,
    household_ids: np.ndarray,
    counts: np.ndarray,
    quantize_weights: bool = True,
) -> UKDataset:
    """A copy of ``dataset`` holding the drawn households, for every year.

    Args:
        dataset: The dataset to subsample. It is not changed.
        household_ids: The identifier of each household that could be drawn.
        counts: The number of times each of those households was drawn.
        quantize_weights: As for ``Simulation.subsample``.
    """
    if isinstance(dataset, UKMultiYearDataset):
        return UKMultiYearDataset(
            datasets=[
                _subsample_single_year_dataset(
                    dataset[year], household_ids, counts, quantize_weights
                )
                for year in dataset.years
            ]
        )
    return _subsample_single_year_dataset(
        dataset, household_ids, counts, quantize_weights
    )


@dataclass
class _Subsample:
    """What one simulation holds once it is subsampled."""

    simulation: "Simulation"
    # The arguments of Simulation.build_from_ids.
    ids: Tuple[np.ndarray, ...]
    # Each supplied input, cut down to the sample.
    inputs: List[Tuple[str, Period, np.ndarray]]
    dataset: Optional[UKDataset]


def _sorted_positions(kept: np.ndarray, ids: np.ndarray) -> np.ndarray:
    """Positions of the kept members of a group population, ordered by
    identifier, which is the order ``Simulation.build_from_ids`` gives them."""
    positions = np.flatnonzero(kept)
    return positions[np.argsort(ids[positions], kind="stable")]


def _plan(
    simulation: "Simulation",
    household_ids: np.ndarray,
    counts: np.ndarray,
    quantize_weights: bool,
    datasets: Dict[int, UKDataset],
) -> _Subsample:
    """Work out the subsample of ``simulation`` without changing it."""
    person = simulation.populations["person"]
    benunit = simulation.populations["benunit"]
    household = simulation.populations["household"]
    if not np.array_equal(np.asarray(household.ids), household_ids):
        raise ValueError(
            "A simulation and its baseline must hold the same households to "
            "be subsampled together."
        )
    person_household = np.asarray(household.members_entity_id)
    person_benunit = np.asarray(benunit.members_entity_id)

    # A benefit unit is kept with its household, so it must sit within one.
    benunit_household = np.full(benunit.count, -1)
    benunit_household[person_benunit] = person_household
    if not np.array_equal(benunit_household[person_benunit], person_household):
        raise ValueError(
            "Cannot subsample: a benefit unit has members in more than one household."
        )
    members = np.bincount(person_household, minlength=household.count)
    if (members[counts > 0] == 0).any():
        raise ValueError("Cannot subsample: a sampled household has no members.")

    entity_counts = {
        "person": counts[person_household],
        "benunit": np.where(benunit_household >= 0, counts[benunit_household], 0),
        "household": counts,
    }
    positions = {
        "person": np.flatnonzero(entity_counts["person"] > 0),
        "benunit": _sorted_positions(
            entity_counts["benunit"] > 0, np.asarray(benunit.ids)
        ),
        "household": _sorted_positions(counts > 0, household_ids),
    }

    inputs = []
    for name, period, values in supplied_input_arrays(simulation):
        entity_key = simulation.tax_benefit_system.get_variable(name).entity.key
        if name in WEIGHT_VARIABLES:
            values = _rescaled(
                name, period, values, entity_counts[entity_key], quantize_weights
            )
        inputs.append((name, period, values[positions[entity_key]]))

    # A simulation and its baseline usually share one dataset object, so
    # subsample each dataset once and share the result in the same way.
    dataset = simulation.dataset
    if dataset is not None:
        if id(dataset) not in datasets:
            datasets[id(dataset)] = subsample_dataset(
                dataset, household_ids, counts, quantize_weights
            )
        dataset = datasets[id(dataset)]

    kept_people = positions["person"]
    return _Subsample(
        simulation=simulation,
        ids=(
            np.asarray(person.ids)[kept_people],
            np.asarray(benunit.ids)[person_benunit[kept_people]],
            household_ids[person_household[kept_people]],
            np.asarray(benunit.ids)[positions["benunit"]],
            household_ids[positions["household"]],
        ),
        inputs=inputs,
        dataset=dataset,
    )


def _apply(
    subsample: _Subsample, simulation: "Simulation", tracer: SimpleTracer
) -> None:
    """Rebuild ``simulation`` on ``subsample``, which was worked out for it
    or for the simulation it is a copy of."""
    start_instant = simulation.start_instant
    # Branches hold the populations the subsample replaces; formulas make
    # them again when they next ask for them.
    simulation.branches = {}
    # The rebuild replaces every stored value, so the record of inputs, and
    # of what was calculated from them, starts again with the inputs it sets.
    simulation._user_input_keys = set()
    simulation._store_history = None
    # A trace of calculations on the replaced populations would otherwise be
    # reported for the sample: a flat trace keeps a variable's first value.
    simulation.tracer = tracer
    simulation.build_from_ids(*subsample.ids)
    for name, period, values in subsample.inputs:
        simulation.set_input(name, period, values)
    simulation.start_instant = start_instant
    # Drop results calculated on the populations the subsample replaced.
    simulation._invalidate_all_caches()
    simulation.dataset = subsample.dataset


def _sampling_weights(simulation: "Simulation", time_period) -> np.ndarray:
    """Household weights for ``time_period``, to draw the sample by.

    A period before the first supplied weights has none: the model would
    return the default weight of one for every household. Use the first
    supplied weights for such a period.
    """
    periods = sorted(
        (
            period
            for name, period, _ in supplied_input_arrays(simulation)
            if name == "household_weight"
        ),
        key=lambda period: period.start,
    )
    if not periods:
        raise ValueError(
            "Cannot subsample a simulation that was given no household_weight values."
        )
    requested = period_(time_period)
    if requested.start < periods[0].start:
        requested = periods[0]
    return np.asarray(simulation.calculate("household_weight", requested))


def subsample_simulation(
    simulation: "Simulation",
    n: Optional[int] = None,
    frac: Optional[float] = None,
    seed=None,
    time_period=None,
    quantize_weights: bool = True,
) -> "Simulation":
    """Subsample ``simulation`` in place; see ``Simulation.subsample``."""
    if not simulation.built_from_dataset:
        raise ValueError("Only a simulation built from a dataset can be subsampled.")
    if simulation.branch_name != "default":
        raise ValueError("Subsample a simulation, not one of its branches.")
    if n is None and frac is None:
        raise ValueError("Either n or frac must be provided.")
    if time_period is None:
        time_period = simulation.default_calculation_period

    weights = _sampling_weights(simulation, time_period)
    if n is None:
        n = int(len(weights) * frac)
    counts = draw_household_counts(
        weights, n, DEFAULT_SEED if seed is None else seed, quantize_weights
    )

    # The baseline is a simulation of its own, with a baseline of its own
    # when this one has a scenario. Give each of them the same households.
    simulations = []
    while simulation is not None and simulation not in simulations:
        simulations.append(simulation)
        simulation = getattr(simulation, "baseline", None)

    # Work out every subsample before changing anything, so that a
    # simulation that cannot be subsampled leaves them all as they were.
    household_ids = np.asarray(simulations[0].populations["household"].ids)
    datasets: Dict[int, UKDataset] = {}
    subsamples = [
        _plan(each, household_ids, counts, quantize_weights, datasets)
        for each in simulations
    ]

    # Each simulation gets a new tracer of the same kind. Simulations that
    # shared a tracer share the new one. The old tracer is kept with its
    # replacement so that its id is not reused while this runs.
    tracers: Dict[int, Tuple[SimpleTracer, SimpleTracer]] = {}

    def new_tracer(old: SimpleTracer) -> SimpleTracer:
        if id(old) not in tracers:
            tracers[id(old)] = (old, type(old)())
        return tracers[id(old)][1]

    first = simulations[0]
    _apply(subsamples[0], first, new_tracer(first.tracer))

    # Replace each baseline with a subsampled copy rather than subsample it
    # in place: policyengine-core's ``clone`` shares a separate baseline, so
    # another simulation can hold this one and still hold every household.
    # Copying each baseline after the simulation that holds it is cut down
    # keeps the memory in use to about what the simulations held before.
    copies = {id(first): first}
    for subsample in subsamples[1:]:
        baseline = subsample.simulation
        copy = baseline.clone(debug=baseline.debug, trace=baseline.trace)
        _apply(subsample, copy, new_tracer(baseline.tracer))
        copies[id(baseline)] = copy
    for each in simulations:
        holder = copies[id(each)]
        baseline = getattr(holder, "baseline", None)
        if baseline is not None and id(baseline) in copies:
            holder.baseline = copies[id(baseline)]
    return first
