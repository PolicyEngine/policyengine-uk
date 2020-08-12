from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

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
        return sum(map(lambda benefit_name : person(benefit_name, period), non_taxable_benefits)) + 12500 / 12

def tax(incomes, bands, rates):
    incomes_ = np.broadcast_to(incomes, (bands.shape[0] - 1, incomes.shape[0]))
    amounts_in_bands = np.clip(incomes_.transpose(), bands[:-1], bands[1:]) - bands[:-1]
    taxes = rates * amounts_in_bands
    total_taxes = taxes.sum(axis=1)
    return total_taxes

class income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Income tax paid per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        estimated_yearly_income = person('taxable_income', period) * 12
        bands = np.array([0, 50000, 150000, np.inf])
        rates = np.array([0.2, 0.4, 0.45])
        return tax(estimated_yearly_income, bands, rates) / 12

class bi_from_pa(Reform):
    def apply(self):
        self.update_variable(income_tax)
        self.update_variable(non_taxable_income)