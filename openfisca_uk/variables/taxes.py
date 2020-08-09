from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

def tax(incomes, bands, rates):
    incomes_ = np.broadcast_to(incomes, (bands.shape[0] - 1, incomes.shape[0]))
    amounts_in_bands = np.clip(incomes_.transpose(), bands[:-1], bands[1:]) - bands[:-1]
    taxes = rates * amounts_in_bands
    total_taxes = taxes.sum(axis=1)
    return total_taxes

class earnings(Variable):
    value_type = float
    entity = Person
    label = u'Amount of earnings per month.'
    definition_period = MONTH

class NI(Variable):
    value_type = float
    entity = Person
    label = u'National Insurance paid per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        bands = np.array([694, 3823, np.inf])
        rates = np.array([0.12, 0.02])
        return tax(person('earnings', period), bands, rates)

class taxable_income(Variable):
    value_type = float
    entity = Person
    label = u'Total taxable income per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        return person('earnings', period) + person('jsa', period)

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
        bands = np.array([12500, 50000, 150000, np.inf])
        rates = np.array([0.2, 0.4, 0.45])
        return tax(estimated_yearly_income, bands, rates) / 12

class net_income(Variable):
    value_type = float
    entity = Person
    label = u'Net income per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        return person('gross_income', period) - person('income_tax', period)