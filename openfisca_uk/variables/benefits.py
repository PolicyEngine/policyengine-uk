from openfisca_core.model_api import *
from openfisca_uk.entities import *

class birth_year(Variable):
    value_type = int
    entity = Person
    label = u'Year of birth'
    definition_period = ETERNITY

class age(Variable):
    value_type = float
    entity = Person
    label = u'Age in years'
    definition_period = YEAR

    def formula(person, period, parameters):
        return int(period.this_year) - person('birth_year', period)

class pension_income(Variable):
    value_type = float
    entity = Person
    label = u'Total pension income between occupational and personal pensions per month'
    definition_period = MONTH

class earnings(Variable):
    value_type = float
    entity = 'Total earnings per month'
    label = u'Label'
    definition_period = MONTH

class JSA_eligible(Variable):
    value_type = bool
    entity = Person
    label = u'Whether eligible for JSA'
    definition_period = MONTH

class JSA_contributory(Variable):
    value_type = float
    entity = Person
    label = u'JSA (contributary) amount received per month'
    definition_period = MONTH

    def formula(person, period, parameters):
        weekly_amount = (person('age', period) >= 18 and person('age', period) < 25) * parameters(period).benefits.JSA.JSA_18_24.yaml + person('age', period) >= 25 * parameters(period).benefits.JSA.JSA_over_25
        weekly_earnings_deduction = max_(0, person('earnings', period) / 4 - parameters(period).benefits.JSA.JSA_earn_disregard)
        weekly_pension_deduction = max_(0, person('earnings', period) / 4 - parameters(period).benefits.JSA.JSA_earn_disregard)
        return max_(0, 4 * (weekly_amount - weekly_earnings_deduction - weekly_pension_deduction) * person('JSA_eligible', period))

class income_support(Variable):
    value_type = float
    entity = Person
    label = u'Income Support amount received per month'
    definition_period = MONTH

class housing_benefit(Variable):
    value_type = float
    entity = Person
    label = u'Housing Benefit amount received per month'
    definition_period = MONTH

class child_benefit(Variable):
    value_type = float
    entity = Person
    label = u'Child Benefit amount received per month'
    definition_period = MONTH

class child_tax_credit(Variable):
    value_type = float
    entity = Person
    label = u'Child Tax Credit amount received per month'
    definition_period = MONTH

class working_tax_credit_childcare(Variable):
    value_type = float
    entity = Person
    label = u'Working Tax Credit (Childcare element) amount received per month'
    definition_period = MONTH

class tax_free_childcare(Variable):
    value_type = float
    entity = Person
    label = u'Tax-Free Childcare amount received per month'
    definition_period = MONTH

class working_tax_credit(Variable):
    value_type = float
    entity = Person
    label = u'Working Tax Credit amount received per month'
    definition_period = MONTH