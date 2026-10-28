"""Sums of money as the model stores them, in pence.

The model stores amounts of money in float32, which holds most of them only
to within half a float32 step: £10,608.52 is stored as 10,608.51953125, and
sums it forms in float32 can lie further from their pence. Rules that turn on
a single penny, such as Carer's Allowance's earnings limit, need the amounts
that were entered, and sums of them worked exactly, not the nearest float32.
"""

from typing import NamedTuple

import numpy as np
from policyengine_core.parameters import get_parameter
from policyengine_core.periods import MONTH, YEAR
from policyengine_core.variables import QuantityType


def stored_pence(amount):
    """``amount``, stored in float32, in pence as float64: the whole number of
    pence it was entered as, where it lies within half a float32 step of one,
    and otherwise its exact value.

    An amount entered in whole pence is stored within half a step of them.
    Below £131,072 a step is under a penny, so no other whole number of pence
    lies that close, and the pence are recovered exactly. An amount with a
    fraction of a penny keeps it, to be rounded as the rule requires, unless
    the fraction is within half a step of a whole penny, which float32 cannot
    tell apart from that penny.
    """
    amount = np.asarray(amount, dtype=np.float32)
    # Float32 has 24 significant bits, so multiplying by 100 in float64 is
    # exact, as are the difference and the half step below.
    pence = amount.astype(np.float64) * 100
    whole = np.round(pence)
    half_step = np.spacing(np.abs(amount)).astype(np.float64) * 50
    return np.where(np.abs(pence - whole) <= half_step, whole, pence)


class Pence(NamedTuple):
    """An amount in pence as float64, with what bounds the float32 rounding
    of the stored amount it was read from: ``bound``, the sum of the
    magnitudes of the stored amounts added to form it, in pounds, and
    ``count``, how many there were."""

    pence: np.ndarray
    bound: np.ndarray
    count: np.ndarray


def stored(amount) -> Pence:
    """``amount``, stored in float32, read with stored_pence."""
    amount = np.asarray(amount, dtype=np.float32)
    return Pence(
        stored_pence(amount),
        np.abs(amount).astype(np.float64),
        np.ones(amount.shape),
    )


def summed(total, parts) -> Pence:
    """``total``, a float32 sum of the stored amounts ``parts`` (each read as
    a Pence, a subtracted one with its pence negated), in pence as float64:
    the exact sum of the parts' pence, where ``total`` lies within the
    rounding of the float32 additions that formed it, and otherwise
    stored(total).

    Summing in float32 rounds at each addition, so a sum of whole-pence
    amounts can lie more than half a step from its pence even when each part
    is recovered exactly; summing the parts' pence in float64 is exact. Each
    of the ``count`` stored amounts lies within half a step of its pence, and
    each addition rounds to within half a step of its result. Every stored
    amount and partial sum is at most ``bound``, up to that rounding, so the
    total lies within ``count`` steps of ``bound`` of the exact sum.
    """
    total = np.asarray(total, dtype=np.float32)
    exact = sum(part.pence for part in parts)
    bound = sum(part.bound for part in parts)
    count = sum(part.count for part in parts)
    # Each rounding is relative, at most 2^-24 of its result, so the partial
    # sums exceed ``bound`` by under count * 2^-23 of it. Take the step of the
    # next float32 up, so that converting to float32 cannot shrink it.
    largest = np.nextafter(
        (bound * (1 + count * 2.0**-23)).astype(np.float32), np.float32(np.inf)
    )
    tolerance = count * np.spacing(largest).astype(np.float64) * 100
    is_sum = np.abs(total.astype(np.float64) * 100 - exact) <= tolerance
    entered = stored(total)
    return Pence(
        np.where(is_sum, exact, entered.pence),
        np.where(is_sum, bound, entered.bound),
        np.where(is_sum, count, entered.count),
    )


def neutralized(simulation, variable, period):
    """Whether policyengine-core gives ``variable`` its default for
    ``period`` without calculating it: neutralized, or abolished by a
    gov.abolitions parameter, read as policyengine-core reads it."""
    try:
        return bool(
            variable.is_neutralized
            or simulation.tax_benefit_system.parameters(period).gov.abolitions[
                variable.name
            ]
        )
    except Exception:
        return False


def supplied(population, variable_name, period):
    """Whether the value of ``variable_name`` for ``period`` was supplied, as
    an input or a value a scenario stored, rather than calculated. A value
    the simulation calculates counts as calculated whether or not its cache
    policy keeps it."""
    holder = population.get_holder(variable_name)
    return period in holder.get_input_periods(population.simulation.branch_name)


def amount_pence(population, variable_name, period):
    """``variable_name`` for ``period``, in pence as float64: as stored_pence
    reads it, except that an amount the model calculated by adding others
    (``adds`` and ``subtracts``) is the exact sum of those amounts, each read
    the same way (see summed), and a monthly flow for a year is the exact
    sum of its months, in whole pence where it lies within the float32
    rounding of a whole penny (see months_summed).

    policyengine-core forms such a sum one addition at a time in float32, so
    a sum of whole-pence amounts can lie more than half a step from its pence.
    Only an addition the simulation calculated itself is redone: a value
    supplied as an input, or stored by a scenario, is read as stored, as is
    one calculated by a formula.
    """
    return _amount(population, variable_name, period).pence


def months_summed(total, months) -> Pence:
    """``total``, policyengine-core's float32 sum of a monthly flow over a
    year, of which ``months`` are the twelve months (each read as a Pence):
    their exact sum, as summed reads it, taken to the nearest whole penny
    where it lies within a float32 step of each month and of the year of
    one.

    policyengine-core divides an amount entered for the year among its months
    in float32, so a month need not lie near whole pence. Each month lies
    within half a step of its share of the year's amount as stored, and that
    within half a step of its pence, so the months' exact sum lies within
    half a step of each month and of the year of the pence entered. Amounts
    entered for each month in whole pence are recovered month by month, and
    their sum is whole pence already.
    """
    exact = summed(total, months)
    steps = sum(part.count * _step(part.bound) for part in months) + _step(exact.bound)
    whole = np.round(exact.pence)
    return Pence(
        np.where(np.abs(exact.pence - whole) <= steps * 100, whole, exact.pence),
        exact.bound,
        exact.count,
    )


def _step(bound):
    """The float32 step, in pounds, of the next float32 above ``bound``, a
    magnitude in pounds as float64: at least that of any float32 up to it."""
    largest = np.nextafter(np.asarray(bound, dtype=np.float32), np.float32(np.inf))
    return np.spacing(largest).astype(np.float64)


def _amount(population, variable_name, period) -> Pence:
    simulation = population.simulation
    variable = simulation.tax_benefit_system.get_variable(variable_name)
    total = population(variable_name, period)
    if neutralized(simulation, variable, period) or supplied(
        population, variable_name, period
    ):
        return stored(total)
    if (
        variable.definition_period == MONTH
        and period.unit == YEAR
        and variable.quantity_type == QuantityType.FLOW
    ):
        # policyengine-core's amount of a monthly flow for a year is the sum
        # of its months'. (Of a stock, it is the last month's, read as
        # stored.)
        return months_summed(
            total,
            [
                _amount(population, variable_name, month)
                for month in period.get_subperiods(MONTH)
            ],
        )
    parts = _summands(simulation, variable, period)
    if parts is None:
        return stored(total)
    read = []
    for name, sign in parts:
        part = _amount(population, name, period)
        read.append(Pence(sign * part.pence, part.bound, part.count))
    return summed(total, read)


def _summands(simulation, variable, period):
    """The amounts the simulation added to calculate ``variable`` for
    ``period``, each with its sign, or None if it did not calculate it by
    adding amounts of the same entity and period."""
    # A variable calculated by a formula lists no amounts to add:
    # policyengine-core allows a variable one way of calculating it. One for
    # another period, or masked by defined_for, is read as stored.
    if variable.defined_for is not None or variable.definition_period != period.unit:
        return None
    summands = []
    for names, sign in ((variable.adds, 1), (variable.subtracts, -1)):
        if isinstance(names, str):
            # A parameter listing the amounts, as policyengine-core reads it.
            names = get_parameter(simulation.tax_benefit_system.parameters, names)(
                period.start
            )
        for name in names or ():
            part = simulation.tax_benefit_system.variables.get(name)
            if part is None or part.entity.key != variable.entity.key:
                # A parameter, or an amount of another entity.
                return None
            summands.append((name, sign))
    return summands or None
