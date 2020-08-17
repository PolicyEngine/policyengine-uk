from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np
import os

dir_path = os.path.dirname(__file__)

def add_bi_to_parameters(parameters):
    file_path = os.path.join(dir_path, 'parameters', 'basic_income.yaml')
    reform_parameters_subtree = load_parameter_file(file_path, name='basic_income')
    parameters.benefits.add_child('basic_income', reform_parameters_subtree)
    return parameters

class basic_income(Variable):
    value_type = float
    entity = Person
    label = u'Basic income per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        return parameters(period).benefits.basic_income * np.ones_like(person)

class non_taxable_income(Variable):
    value_type = float
    entity = Person
    label = u'Total non-taxable income per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        non_taxable_benefits = [
            'income_support',
            'housing_benefit',
            'child_benefit',
            'child_tax_credit',
            'working_tax_credit_childcare',
            'tax_free_childcare',
            'working_tax_credit',
            'basic_income'
        ]
        return sum(map(lambda benefit_name : person(benefit_name, period), non_taxable_benefits))

class income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Income tax paid per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        estimated_yearly_income = person('taxable_income', period) * 12
        return parameters(period).taxes.income_tax.calc(estimated_yearly_income) / 12

class bi_from_pa(Reform):
    def apply(self):
        self.add_variable(basic_income)
        self.modify_parameters(add_bi_to_parameters)
        self.update_variable(income_tax)
        self.update_variable(non_taxable_income)