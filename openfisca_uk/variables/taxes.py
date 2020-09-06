from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

# Input variables

## Person

class pension_income(Variable):
    value_type = float
    entity = Person
    label = u'Total pension income between occupational and personal pensions per week'
    definition_period = ETERNITY

class employee_earnings(Variable):
    value_type = float
    entity = Person
    label = u'Total earnings per week from employment'
    definition_period = ETERNITY

class self_employed_earnings(Variable):
    value_type = float
    entity = Person
    label = u'Total earnings per week from self-employment'
    definition_period = ETERNITY

class investment_income(Variable):
    value_type = float
    entity = Person
    label = u'Total earnings per week from investments'
    definition_period = ETERNITY

# Derived variables

## Person

class total_earnings(Variable):
    value_type = float
    entity = Person
    label = u'Total earnings per week from employment, self-employment, investments and pensions'
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person('employee_earnings', period) + person('self_employed_earnings', period) + person('investment_income', period)

class income(Variable):
    value_type = float
    entity = Person
    label = u'Total taxable income per week'
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return max_(person('employee_earnings', period) + person('self_employed_earnings', period) + person('pension_income', period) + person('investment_income', period), 0)

class taxable_income(Variable):
    value_type = float
    entity = Person
    label = u'Total taxable income per week'
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return max_(person('employee_earnings', period) + person('self_employed_earnings', period) + 0.75 * person('pension_income', period) + person('investment_income', period), 0)

class NI(Variable):
    value_type = float
    entity = Person
    label = u'National Insurance paid per week'
    definition_period = ETERNITY
    reference = ['https://www.gov.uk/national-insurance']
    def formula(person, period, parameters):
        employee_NI = parameters(period).taxes.national_insurance.employee_rates.calc(person('employee_earnings', period))
        estimated_yearly_self_emp = person('self_employed_earnings', period) * 52
        self_employed_NI_basic = parameters(period).taxes.national_insurance.self_employed_basic * (estimated_yearly_self_emp > parameters(period).taxes.national_insurance.self_employed_basic_threshold)
        self_employed_NI_higher = parameters(period).taxes.national_insurance.self_employed_higher.calc(estimated_yearly_self_emp)
        return employee_NI + self_employed_NI_basic + self_employed_NI_higher
    
class income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Income tax paid per week'
    definition_period = ETERNITY

    def formula(person, period, parameters):
        estimated_yearly_income = person('taxable_income', period) * 52
        pa_deduction = parameters(period).taxes.income_tax.personal_allowance_deduction.calc(estimated_yearly_income)
        x = parameters(period).taxes.income_tax.income_tax.calc(estimated_yearly_income + pa_deduction) / 52
        return x

class net_income(Variable):
    value_type = float
    entity = Person
    label = u'Net income per week'
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person('income', period) - person('income_tax', period) - person('NI', period)

class effective_tax_rate(Variable):
    value_type = float
    entity = Person
    label = u'Net income per week'
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return where(person('income', period) == 0, 0, 1 - person('net_income', period) / person('income', period))