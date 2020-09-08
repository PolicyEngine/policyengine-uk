from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np
import os

dir_path = os.path.dirname(__file__)

def add_basic_income_params(parameters):
    basic_income_subtree = load_parameter_file(os.path.join(dir_path, "parameters", "basic_income"))
    parameters.benefits.add_child("basic_income", basic_income_subtree)
    return parameters

class basic_income(Variable):
    value_type = float
    entity = Person
    label = u'Amount of basic income per week'
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person('is_senior', period) * parameters(period).benefits.basic_income.senior_amount + person('is_adult', period) * parameters(period).benefits.basic_income.adult_amount + person('is_child', period) * parameters(period).benefits.basic_income.child_amount

class family_basic_income(Variable):
    value_type = float
    entity = Family
    label = u'Amount of basic income per week, per household'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.sum(family.members('basic_income', period))

class family_total_income(Variable):
    value_type = float
    entity = Family
    label = u'Amount of total income per week across the family'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family('family_earnings', period) + family('family_pension_income', period) + max_(0, family('family_basic_income', period) - parameters(period).benefits.basic_income.income_disregard)

class basic_income_reform(Reform):
    def apply(self):
        self.modify_parameters(add_basic_income_params)
        self.add_variable(basic_income)
        self.add_variable(family_basic_income)
        self.update_variable(family_total_income)