from openfisca_core.model_api import *
from openfisca_uk.entities import *

# Input variables

## Person

class birth_year(Variable):
    value_type = int
    entity = Person
    label = u'Year of birth'
    definition_period = ETERNITY

class JSA_contrib_eligible(Variable):
    value_type = bool
    entity = Person
    label = u'Whether eligible for JSA (contributory)'
    definition_period = MONTH

class JSA_income_eligible(Variable):
    value_type = bool
    entity = Person
    label = u'Whether eligible for JSA (income-based)'
    definition_period = MONTH

class income_support_eligible(Variable):
    value_type = bool
    entity = Person
    label = u'Whether eligible for Income Support'
    definition_period = MONTH

class housing_benefit_eligible(Variable):
    value_type = bool
    entity = Person
    label = u'Whether eligible for Housing Benefit'
    definition_period = MONTH

class child_benefit_eligible(Variable):
    value_type = bool
    entity = Person
    label = u'Whether eligible for Child Benefit'
    definition_period = MONTH

class child_tax_credit_eligible(Variable):
    value_type = bool
    entity = Person
    label = u'Whether eligible for Child Tax Credit'
    definition_period = MONTH

class working_tax_credit_eligible(Variable):
    value_type = bool
    entity = Person
    label = u'Whether eligible for Working Tax Credit'
    definition_period = MONTH

class housing_benefit_eligible(Variable):
    value_type = bool
    entity = Person
    label = u'Whether eligible for JSA (income-based)'
    definition_period = MONTH

# Derived variables

class age(Variable):
    value_type = float
    entity = Person
    label = u'Age in years'
    definition_period = YEAR

    def formula(person, period, parameters):
        return int(period.this_year) - person('birth_year', period)

class JSA_contributory(Variable):
    value_type = float
    entity = Person
    label = u'JSA (contributary) amount received per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        weekly_amount = (person('age', period) >= 18 and person('age', period) < 25) * parameters(period).benefits.JSA.JSA_contrib_18_24.yaml + person('age', period) >= 25 * parameters(period).benefits.JSA.JSA_over_25
        weekly_earnings_deduction = max_(0, person('earnings', period) / 4 - parameters(period).benefits.JSA.JSA_earn_disregard)
        weekly_pension_deduction = max_(0, person('earnings', period) / 4 - parameters(period).benefits.JSA.JSA_earn_disregard)
        return max_(0, 4 * (weekly_amount - weekly_earnings_deduction - weekly_pension_deduction) * person('JSA_eligible', period))