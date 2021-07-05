from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np
from datetime import datetime
from pathlib import Path

DATA_FOLDER = Path(__file__).parent.parent / "data"

np.random.seed(0)


def add(entity, period, variable_names, options=None):
    """Sums a list of variables over entities.

    Args:
        entity (Entity): Either person, benunit or household
        period (Period): The period to calculate over
        variable_names (list): A list of variable names
        options (list, optional): The options to use - ADD, DIVIDE or MATCH to define period mismatch behaviour. Defaults to None.

    Returns:
        Array: Array of entity values.
    """
    return sum(
        map(lambda var: entity(var, period, options=options), variable_names)
    )


def aggr(entity, period, variable_names, options=None):
    """Sums a list of variables over each member of a group.

    Args:
        entity (Entity): Either benunit or household
        period (Period): The period to calculate over
        variable_names (list): A list of variable names
        options (list, optional): The options to use - ADD, DIVIDE or MATCH to define period mismatch behaviour. Defaults to None.

    Returns:
        Array: Array of entity values.
    """
    return sum(
        map(
            lambda var: entity.sum(
                entity.members(var, period, options=options)
            ),
            variable_names,
        )
    )


def aggr_max(entity, period, variable_names, options=None):
    """Finds the maximum of a list of variables over each member of a group.

    Args:
        entity (Entity): Either benunit or household
        period (Period): The period to calculate over
        variable_names (list): A list of variable names
        options (list, optional): The options to use - ADD, DIVIDE or MATCH to define period mismatch behaviour. Defaults to None.

    Returns:
        Array: Array of entity values.
    """
    return sum(
        map(
            lambda var: entity.max(
                entity.members(var, period, options=options)
            ),
            variable_names,
        )
    )


def select(conditions, choices):
    """Selects the corresponding choice for the first matching condition in a list.

    Args:
        conditions (list): A list of boolean arrays
        choices (list): A list of arrays

    Returns:
        Array: Array of values
    """
    return np.select(conditions, choices)


clip = np.clip
inf = np.inf

WEEKS_IN_YEAR = 52
MONTHS_IN_YEAR = 12


def amount_over(amount, threshold):
    return max_(0, amount - threshold)


def amount_between(amount, threshold_1, threshold_2):
    return clip(amount, threshold_1, threshold_2) - threshold_1


def random(entity, reset=True):
    x = np.random.rand(entity.count)
    if reset:
        np.random.seed(0)
    return x


def is_in(values, *targets):
    return sum(map(lambda target: values == target, targets))
