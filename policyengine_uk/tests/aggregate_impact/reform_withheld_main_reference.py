"""Frozen reform withholding from main (da31e8698), with commentary omitted.

Keep this independent of the production tool: it is the differential oracle
for #2654, which records why a reform year is withheld and must not change
which years are withheld.
"""

from typing import Mapping, Optional

import numpy as np

MIN_CELL = 10
CHANGE_GBP = 0.005


def small(count: int) -> bool:
    return 0 < count < MIN_CELL


def array(sim, variable: str, period, map_to: Optional[str] = None) -> np.ndarray:
    try:
        result = sim.calculate(variable, period, map_to=map_to, unweighted=True)
    except TypeError:
        result = sim.calculate(variable, period, map_to=map_to)
    return np.asarray(getattr(result, "values", result))


def entity_of(sim, variable: str) -> str:
    return sim.tax_benefit_system.variables[variable].entity.key


def to_household(sim, values: np.ndarray, entity: str) -> np.ndarray:
    if entity == "household":
        return np.asarray(values, dtype=np.float64)
    return np.asarray(
        sim.map_result(np.asarray(values, dtype=np.float64), entity, "household"),
        dtype=np.float64,
    )


def _weighted_records(mask, weight) -> int:
    return int(np.count_nonzero(np.asarray(mask) & (np.asarray(weight) > 0)))


def reform_withheld(
    reformed, year: int, baseline: Optional[Mapping], components
) -> bool:
    if baseline is None:
        return True
    for variable, before in baseline["hidden"].items():
        if not np.array_equal(
            array(reformed, variable, year).astype(np.float64), before
        ):
            return True
    weights = {}

    def weight(variable):
        entity = entity_of(reformed, variable)
        if entity not in weights:
            weights[entity] = array(reformed, f"{entity}_weight", year).astype(
                np.float64
            )
        return weights[entity]

    for variable in components:
        if variable in baseline["hidden"]:
            continue
        values = array(reformed, variable, year).astype(np.float64)
        if small(_weighted_records(values != 0, weight(variable))):
            return True
    balance = to_household(
        reformed,
        array(reformed, "gov_balance", year).astype(np.float64),
        entity_of(reformed, "gov_balance"),
    )
    changed = np.abs(balance - baseline["balance"]) > CHANGE_GBP
    if small(_weighted_records(changed, baseline["household_weight"])):
        return True
    for variable, before in baseline["targets"].items():
        after = array(reformed, variable, year).astype(np.float64)
        if small(
            _weighted_records(np.abs(after - before) > CHANGE_GBP, weight(variable))
        ):
            return True
    return False
