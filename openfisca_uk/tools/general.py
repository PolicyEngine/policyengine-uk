from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np


def add(entity, period, variable_names, options=None):
    return sum(
        map(lambda var: entity(var, period, options=options), variable_names)
    )


def aggr(entity, period, variable_names, options=None):
    return sum(
        map(
            lambda var: entity.sum(
                entity.members(var, period, options=options)
            ),
            variable_names,
        )
    )


def aggr_max(entity, period, variable_names, options=None):
    return sum(
        map(
            lambda var: entity.max(
                entity.members(var, period, options=options)
            ),
            variable_names,
        )
    )


def select(conditions, choices):
    return np.select(conditions, choices)
