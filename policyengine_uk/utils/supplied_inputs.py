"""Read Core-owned supplied inputs, with UK neutralization semantics.

Core keeps input provenance and holder storage consistent for every variable,
including direct public holder writes/deletions, clones and branch snapshots.
Carried values and formula outputs are not supplied inputs. These helpers do
not maintain a parallel index or repair caches during calculation.
"""

from typing import List, Optional

import numpy as np
from policyengine_core.periods import Period


def supplied_input_periods(population, variable_name: str) -> List[Period]:
    """Periods for which ``variable_name`` was supplied as an input, on this
    branch or one it was made from, earliest first."""
    return population.simulation.supplied_input_periods(variable_name)


def supplied_input(
    population, variable_name: str, period: Period
) -> Optional[np.ndarray]:
    """The value of ``variable_name`` for ``period`` if it was supplied as an
    input, on this branch or the nearest one it was made from; otherwise
    None. A value the engine carried over from an earlier period, or cached
    after a calculation, is not an input."""
    simulation = population.simulation
    value = simulation.get_supplied_input(variable_name, period)
    if value is None:
        return None
    # A neutralized variable reads as its default, as it does through the
    # engine. (PolicyEngine-UK builds no gov.abolitions parameters, so there is
    # no abolition switch to honour here.)
    variable = simulation.tax_benefit_system.get_variable(variable_name)
    if variable.is_neutralized:
        return population.get_holder(variable_name).default_array()
    return value
