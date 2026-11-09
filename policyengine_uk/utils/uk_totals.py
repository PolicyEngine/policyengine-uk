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

from typing import List

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
