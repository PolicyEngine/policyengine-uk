from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np


class HHINC(Variable):
    value_type = float
    entity = Household
    label = u"Gross household income FRS variable"
    definition_period = ETERNITY


class council_tax(Variable):
    value_type = float
    entity = Household
    label = u"Council Tax amount per week"
    definition_period = ETERNITY


class housing_cost(Variable):
    value_type = float
    entity = Household
    label = u"Housing costs per week"
    definition_period = ETERNITY


class household_gross_income(Variable):
    value_type = float
    entity = Household
    label = u"Gross household income per week"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.sum(household.members("gross_income", period))


class household_net_income_bhc(Variable):
    value_type = float
    entity = Household
    label = u"Net household income per week, before housing costs"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.sum(
            household.members("net_income", period)
        ) - household("council_tax", period)


class equiv_household_net_income_bhc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalised net household income per week, before housing costs"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household("household_net_income_bhc", period) / household(
            "household_equivalisation", period
        )


class household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Net household income per week, after housing costs"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return (
            household.sum(household.members("net_income", period))
            - household("council_tax", period)
            - household("housing_cost", period)
        )


class equiv_household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalised net household income per week, after housing costs"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household("household_net_income_ahc", period) / household(
            "household_equivalisation", period
        )
