"""Branches of a simulation that hold only some of its households.

A comparison that concerns a few households can run in a branch holding only
them, at a cost in proportion to those households rather than to the whole
population. Each household is worked out from its own members' values,
except in the formulas that read the whole population
(WHOLE_POPULATION_VARIABLES), which would give other values in a subset.

The branch starts from every value the simulation holds for those
households, inputs and calculated values alike, so what the simulation has
already worked out is not worked out again, and a value calculated in the
subset is the one the whole simulation would calculate.
"""

from contextlib import contextmanager
from typing import Optional

import numpy as np

# Every formula that reads the whole population: a weighted total, a weighted
# rank or median, or records spread by weight over the dataset. A household
# subset takes each person's months_since_last_birthday from the whole
# population (whole_population_value). None of the others feeds income tax or
# any benefit, so the property allowance election never computes them. Two
# tests in test_household_subset.py keep it so: one fails if a formula reads a
# population weight and is not listed here, or is listed and no longer reads
# one; the other fails if income tax, with the winter fuel payment charge and
# the benefits the charge reads, computes any of them but those in
# TAKEN_FROM_WHOLE_POPULATION. A formula that comes to need one of them there
# has to take its whole-population value, as months_since_last_birthday does.
WHOLE_POPULATION_VARIABLES = frozenset(
    {
        "attends_private_school",
        "carbon_tax",
        "consumer_incident_tax_revenue_change",
        "consumption_shareholding",
        "corporate_land_value",
        "education_budget_change",
        "employer_ni_response_capital_incidence",
        "employer_ni_response_consumer_incidence",
        "household_income_decile",
        "household_income_decile_ahc",
        "household_wealth_decile",
        "in_relative_poverty_ahc",
        "in_relative_poverty_bhc",
        "months_since_last_birthday",
        "nhs_budget_change",
        "other_public_spending_budget_change",
        "pre_budget_change_ons_household_income_decile",
        "shareholding",
    }
)
# Those a household subset takes from the whole population.
TAKEN_FROM_WHOLE_POPULATION = frozenset({"months_since_last_birthday"})

# The attribute of a household subset (and of each branch made from it, which
# copies its attributes) naming the simulation it was made from and the
# positions there of the people it holds.
WHOLE_POPULATION = "_household_subset_of"


class HouseholdSubset:
    """A simulation holding some of another's households, and where their
    people are in it.

    ``simulation`` is the branch holding the households, or the simulation
    itself where it already holds no others or a subset cannot be made.
    ``person`` holds the positions of the branch's people in the simulation,
    or None where ``simulation`` is the simulation itself.
    """

    def __init__(self, simulation, person: Optional[np.ndarray], count: int):
        self.simulation = simulation
        self.person = person
        self.count = count

    def take(self, values: np.ndarray) -> np.ndarray:
        """The subset's people's values from an array over everyone."""
        return values if self.person is None else values[self.person]

    def expand(self, values: np.ndarray) -> np.ndarray:
        """An array over everyone from the subset's people's values, with
        nil for the people the subset leaves out."""
        if self.person is None:
            return values
        result = np.zeros(self.count, dtype=np.asarray(values).dtype)
        result[self.person] = values
        return result


@contextmanager
def household_subset(simulation, name: str, people: np.ndarray):
    """A HouseholdSubset of ``simulation`` holding the households of the
    people where ``people`` is true, dropped when the block ends.

    Where every household is kept, or a subset cannot be made (a value kept
    on disk, a benefit unit or other group spanning households kept and left
    out, or a baseline holding other people), it is the simulation itself.
    """
    households = simulation.populations["household"].any(np.asarray(people, dtype=bool))
    count = simulation.populations["person"].count
    made = []
    try:
        subset = None
        if not households.all():
            subset = _subset(simulation, name, households, made)
        if subset is None:
            # Drop any branch made before the subset turned out impossible.
            _drop(made)
            made.clear()
            yield HouseholdSubset(simulation, None, count)
        else:
            branch, person = subset
            yield HouseholdSubset(branch, person, count)
    finally:
        _drop(made)


def whole_population_value(population, variable: str, period):
    """In a household subset, the value of ``variable`` for each member of
    ``population`` in the whole population; None elsewhere."""
    whole = getattr(population.simulation, WHOLE_POPULATION, None)
    if whole is None:
        return None
    source, positions = whole
    return source.populations[population.entity.key](variable, period)[
        positions[population.entity.key]
    ]


def _subset(simulation, name, households, made):
    """The branch holding the kept households and the positions of its people
    in ``simulation``, or None where it cannot be made. Records each branch
    it makes in ``made``."""
    positions = _positions(simulation, households)
    if positions is None:
        return None
    memo = {}
    branch = _restricted_branch(simulation, name, positions, made, memo)
    if branch is None:
        return None
    return branch, positions["person"]


def _positions(simulation, households):
    """For each population, the positions of the entities in the kept
    households, or None where a group has members in kept and left out
    households."""
    people = simulation.populations["household"].members_entity_id
    kept_people = households[people]
    positions = {"person": np.flatnonzero(kept_people)}
    for key, population in simulation.populations.items():
        if key == "person":
            continue
        members = np.asarray(population.members_entity_id)
        kept = np.zeros(population.count, dtype=bool)
        kept[members[kept_people]] = True
        if (kept[members] != kept_people).any():
            return None
        positions[key] = np.flatnonzero(kept)
    return positions


def _restricted_branch(simulation, name, positions, made, memo):
    """A branch of ``simulation`` holding the entities at ``positions``, with
    a baseline restricted to the same entities, or None where it cannot be
    made."""
    if id(simulation) in memo:
        return memo[id(simulation)]
    if any(
        holder._disk_storage is not None
        for population in simulation.populations.values()
        for holder in population._holders.values()
    ):
        return None
    while name in simulation.branches or name == simulation.branch_name:
        name += "_"
    branch = simulation.get_branch(name)
    made.append((simulation, name))
    memo[id(simulation)] = branch
    if not _restrict(branch, positions):
        return None
    branch.macro_cache_read = False
    setattr(branch, WHOLE_POPULATION, (simulation, positions))
    baseline = getattr(simulation, "baseline", None)
    if baseline is not None and baseline is not simulation:
        if any(
            baseline.populations[key].count != population.count
            or not np.array_equal(baseline.populations[key].ids, population.ids)
            for key, population in simulation.populations.items()
        ):
            return None
        restricted = _restricted_branch(baseline, name, positions, made, memo)
        if restricted is None:
            return None
        branch.baseline = restricted
    return branch


def _restrict(branch, positions) -> bool:
    """Keep only the entities at ``positions`` in a new branch: its
    populations and every value it holds. False where a held value is not one
    per entity."""
    people = positions["person"]
    for key, population in branch.populations.items():
        kept = positions[key]
        for holder in population._holders.values():
            storage = holder._memory_storage
            for storage_key, values in list(storage._arrays.items()):
                if np.ndim(values) != 1 or len(values) != population.count:
                    return False
                storage._arrays[storage_key] = values[kept]
            # The branch's arrays are its own copies now, not views of its
            # parent's (see InMemoryStorage.clone).
            storage.__dict__.pop("_shared", None)
        if key != "person":
            new_position = np.full(population.count, -1)
            new_position[kept] = np.arange(len(kept))
            population.members_entity_id = new_position[
                np.asarray(population.members_entity_id)[people]
            ]
            if population._members_role is not None:
                population._members_role = population._members_role[people]
            if population._members_position is not None:
                population._members_position = population._members_position[people]
            population._ordered_members_map = None
        population.ids = np.asarray(population.ids)[kept]
        population.count = len(kept)
    # Values a scenario stored as the model's (see utils.supplied_inputs).
    model_values = getattr(branch, "_model_values", None)
    if model_values:
        for key, values in list(model_values.items()):
            entity = branch.tax_benefit_system.get_variable(key[0]).entity.key
            model_values[key] = values[positions[entity]]
    branch._fast_cache = {}
    return True


def _drop(made) -> None:
    """Drop the branches made for a subset, the latest first."""
    for simulation, name in reversed(made):
        simulation.branches.pop(name, None)
