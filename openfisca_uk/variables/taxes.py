from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

class total_income(Variable):
    value_type = float
    entity = Person
    label = u'Total amount of income per month.'
    definition_period = MONTH

class NI(Variable):
    value_type = float
    entity = Person
    label = u'National Insurance paid per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        return parameters(period).taxes.national_insurance.calc(person('total_income', period))

class taxable_income(Variable):
    value_type = float
    entity = Person
    label = u'Total taxable income per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        return person('total_income', period) + person('jsa', period)

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
            'working_tax_credit'
        ]
        return sum(map(lambda benefit_name : person(benefit_name, period), non_taxable_benefits))

class gross_income(Variable):
    value_type = float
    entity = Person
    label = u'Gross income per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        return person('taxable_income', period) + person('non_taxable_income', period)
    
class income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Income tax paid per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        estimated_yearly_income = person('taxable_income', period) * 12
        pa_deduction = parameters(period).taxes.personal_allowance_deduction.calc(estimated_yearly_income)
        return parameters(period).taxes.income_tax.calc(estimated_yearly_income + pa_deduction) / 12

class effective_tax_rate(Variable):
    value_type = float
    entity = Person
    label = u'Effective income tax rate'
    definition_period = MONTH

    def formula(person, period, parameters):
        return where(person('total_income', period) == 0, 0, person('income_tax', period) / person('total_income', period))

class net_income(Variable):
    value_type = float
    entity = Person
    label = u'Net income per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        return person('gross_income', period) - person('income_tax', period) - person('NI', period)

class household_net_income(Variable):
    value_type = float
    entity = Household
    label = u'Net income per month per household'
    definition_period = MONTH

    def formula(household, period, parameters):
        households = household.members('net_income', period)
        return household.sum(household.members('net_income', period))