from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np


class council_tax(Variable):
    value_type = float
    entity = Household
    label = u"Council Tax amount per week"
    definition_period = ETERNITY


class housing_costs(Variable):
    value_type = float
    entity = Household
    label = u"Housing costs per week"
    definition_period = ETERNITY


class service_charges(Variable):
    value_type = float
    entity = Household
    label = u"Amount paid for Service Charges/Ground Rent"
    definition_period = ETERNITY

class household_earned_income(Variable):
    value_type = float
    entity = Household
    label = u'Earned household income per week'
    definition_period = ETERNITY

    def formula(household, period, parameters):
        COMPONENTS = [
            "employee_earnings",
            "self_employed_earnings",
            "pension_income",
            "interest"
        ]
        return sum(map(lambda component : household.sum(household.members(component, period)), COMPONENTS))

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
        return (
            household.sum(household.members("net_income", period))
            - household("council_tax", period)
            - household("service_charges", period)
        )


class equiv_household_net_income_bhc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalised net household income per week, before housing costs"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household("household_net_income_bhc", period) / household(
            "household_equivalisation_bhc", period
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
            - household("housing_costs", period)
            - household("service_charges", period)
        )


class equiv_household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalised net household income per week, after housing costs"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household("household_net_income_ahc", period) / household(
            "household_equivalisation_ahc", period
        )
