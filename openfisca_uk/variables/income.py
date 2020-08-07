from openfisca_core.model_api import *
from openfisca_uk.entities import *

class income(Variable):
    value_type = float
    entity = Person
    label = u'Yearly gross income'
    definition_period = YEAR

class personal_allowance(Variable):
    value_type = float
    entity = Person
    label = u'Yearly personal allowance'
    definition_period = YEAR

    def formula(person, period, parameters):
        is_married = person.marriage.nb_persons() > 1
        partner_income = person.marriage.sum(person.marriage.members('income', period)) - person('income', period)
        partner_transferable_allowance = min_(max_(12500 - partner_income, 0), 1250)
        self_transferable_allowance = min_(max_(12500 - person('income', period), 0), 1250)
        amount_over_100k = max_(person('income', period) - 100000, 0)
        single_personal_allowance = max_(min_(person('income', period), 12500) - 0.5 * amount_over_100k, 0)
        return where(is_married, max_(single_personal_allowance + partner_transferable_allowance - self_transferable_allowance, 0), single_personal_allowance) 

class taxable_income(Variable):
    value_type = float
    entity = Person
    label = u'Yearly income after personal allowance is deducted'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person('income', period) - person('personal_allowance', period)

class basic_rate_tax(Variable):
    value_type = float
    entity = Person
    label = u'Yearly basic rate income tax'
    definition_period = YEAR

    def formula(person, period, parameters):
        return 0.2 * min_(max_(person('income', period) - person('personal_allowance', period), 0), 50000 - 12500)

class higher_rate_tax(Variable):
    value_type = float
    entity = Person
    label = u'Yearly higher rate income tax'
    definition_period = YEAR

    def formula(person, period, parameters):
        return 0.4 * min_(max_(person('income', period) - 50000, 0), 150000 - 50000)

class additional_rate_tax(Variable):
    value_type = float
    entity = Person
    label = u'Yearly additional rate income tax'
    definition_period = YEAR

    def formula(person, period, parameters):
        return 0.45 * max_(person('income', period) - 150000, 0)

class income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Yearly income tax'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person('basic_rate_tax', period) + person('higher_rate_tax', period) + person('additional_rate_tax', period)

class post_tax_income(Variable):
    value_type = float
    entity = Person
    label = u'Yearly post-tax income'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person('income', period) - person('income_tax', period)

class marriage_post_tax_income(Variable):
    value_type = float
    entity = Marriage
    label = u'Yearly post-tax income for a married couple'
    definition_period = YEAR

    def formula(marriage, period, parameters):
        return marriage.sum(marriage.members('post_tax_income', period))