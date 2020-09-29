from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np


class household_weight(Variable):
    value_type = float
    entity = Household
    label = u"Weighting of the household"
    definition_period = ETERNITY


class household_equivalisation(Variable):
    value_type = float
    entity = Household
    label = u"Equivalisation factor to account for household composition"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        second_adult = household.nb_persons(Household.ADULT) == 2
        num_young_children = household.sum(
            household.members("is_young_child", period)
        )
        num_older_children = household.sum(
            household.members("is_older_child", period)
        )
        weighting = (
            0.67
            + 0.33 * second_adult
            + 0.33 * num_older_children
            + 0.2 * num_young_children
        )
        return weighting


class people_in_household(Variable):
    value_type = int
    entity = Household
    label = u"Number of people in the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.nb_persons()


class adults_in_household(Variable):
    value_type = int
    entity = Household
    label = u"Number of adults in the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.nb_persons(Household.ADULT)


class children_in_household(Variable):
    value_type = int
    entity = Household
    label = u"Number of children in the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.nb_persons(Household.CHILD)
