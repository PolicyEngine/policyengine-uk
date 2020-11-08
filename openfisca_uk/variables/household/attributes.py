from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np


class household_weight(Variable):
    value_type = float
    entity = Household
    label = u"Weighting of the household"
    definition_period = ETERNITY


class household_equivalisation_bhc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalisation factor to account for household composition, before housing costs"
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


class household_equivalisation_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalisation factor to account for household composition, after housing costs"
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
            0.58
            + 0.42 * second_adult
            + 0.42 * num_older_children
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
        return household.sum(household.members("is_adult", period))


class working_age_adults_in_household(Variable):
    value_type = int
    entity = Household
    label = u"Number of adults in the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.sum(household.members("is_working_age_adult", period))


class children_in_household(Variable):
    value_type = int
    entity = Household
    label = u"Number of children in the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.nb_persons(Household.CHILD)


class seniors_in_household(Variable):
    value_type = int
    entity = Household
    label = u"Number of senior citizens in the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.sum(household.members("is_state_pension_age", period))


class household_archetype(Variable):
    value_type = int
    entity = Household
    label = u"Coded archetype of the household"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        num_adults = household.sum(
            household.members("is_working_age_adult", period)
        )
        num_children = household.sum(household.members("is_child", period))
        num_seniors = household.sum(household.members("is_senior", period))
        return num_seniors * 100 + num_adults * 10 + num_children


class region(Variable):
    value_type = float
    entity = Household
    label = u"FRS-coded region of the UK"
    definition_period = ETERNITY
