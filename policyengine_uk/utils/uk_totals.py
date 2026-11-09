"""UK totals of the keys that shares of national totals are taken by.

shareholding and consumption_shareholding give each household its share of a
UK total: of corporate_sector_wealth and of consumption, summed over all UK
households at their weights. A simulation of all UK households can sum them
itself. A simulation of part of the UK cannot, because the other households
are not in it: a region filtered from the data, an extract, a household subset
or one block of a larger build. So whoever holds the whole population writes
the totals into the data, as household columns the same on every row, and the
shares divide by them (policyengine-uk#2896).

The columns hold the totals of each key's components, the variables the key
adds, so the formulas derive the key's total, and the UK's carbon emissions,
with the simulation's own definitions and parameters. Each column is uprated
like the column it sums, times population (create_uk_total_growth).
"""

from typing import Dict, List

import numpy as np

from policyengine_uk.utils.carbon import CARBON_CATEGORIES, carbon_intensities

PREFIX = "uk_total_"
KEYS = ("corporate_sector_wealth", "consumption")


def components(key: str) -> List[str]:
    """The variables ``key`` adds, whose UK totals the data can carry."""
    if key == "corporate_sector_wealth":
        from policyengine_uk.variables.household.wealth.corporate_sector_wealth import (
            corporate_sector_wealth as variable,
        )
    elif key == "consumption":
        from policyengine_uk.variables.input.consumption.consumption import (
            consumption as variable,
        )
    else:
        raise ValueError(f"{key} is not a key with UK totals.")
    return list(variable.adds)


def total_name(component: str) -> str:
    """The input holding the UK total of ``component``."""
    return PREFIX + component


def carried_uk_total(population, key: str, period) -> np.ndarray:
    """Each household's carried UK total of ``key``: the sum of its
    components' carried totals, 0 where the data carries none."""
    return sum(
        population(total_name(component), period) for component in components(key)
    )


def carried_uk_emissions(population, period, parameters) -> np.ndarray:
    """The carbon emissions of all UK households from the carried totals of
    their spending, at this simulation's carbon intensities: each category's
    UK total times its intensity, as carbon_consumption works out each
    household's. 0 where the data carries no spending totals."""
    return sum(
        population(total_name(category), period) * intensity
        for category, intensity in zip(
            CARBON_CATEGORIES, carbon_intensities(parameters, period)
        )
    )


def uk_total_columns() -> List[str]:
    """The inputs that carry the UK totals, in key order."""
    return [total_name(component) for key in KEYS for component in components(key)]


def uk_totals(household) -> Dict[str, float]:
    """The UK total of each key component over a table of households, at its
    ``household_weight``: the values add_uk_totals writes. A table without
    weights weighs each household 1, as household_weight's default does. A
    component the table lacks totals 0. The table must hold every UK
    household."""
    weight = (
        np.asarray(household["household_weight"], dtype=float)
        if "household_weight" in household
        else np.ones(len(household))
    )
    totals = {}
    for key in KEYS:
        for component in components(key):
            values = (
                np.asarray(household[component], dtype=float)
                if component in household
                else np.zeros_like(weight)
            )
            totals[total_name(component)] = float(np.sum(values * weight))
    return totals


def add_uk_totals(dataset):
    """A copy of ``dataset`` whose households carry their UK totals.

    Call it on a dataset holding every UK household, before taking any part
    of it: a region, an extract, a household subset or a block of a build.
    The totals are written at the dataset's year, and a simulation projects
    them with the data. A multi-year dataset's years each carry their own.
    """
    from policyengine_uk.data.dataset_schema import (
        UKMultiYearDataset,
        UKSingleYearDataset,
    )

    if isinstance(dataset, UKMultiYearDataset):
        return UKMultiYearDataset(
            datasets=[add_uk_totals(dataset[year]) for year in dataset.years]
        )
    if not isinstance(dataset, UKSingleYearDataset):
        raise TypeError(
            "add_uk_totals takes a UKSingleYearDataset or UKMultiYearDataset, "
            f"not {type(dataset).__name__}."
        )
    new = dataset.copy()
    new.household = new.household.assign(**uk_totals(new.household))
    return new
