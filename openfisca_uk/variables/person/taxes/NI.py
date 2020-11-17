from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class NI_class_1(Variable):
    value_type = float
    entity = Person
    label = u'National Insurance (Class 1)'
    definition_period = YEAR
    reference = u'https://www.gov.uk/national-insurance'

    def formula(person, period, parameters):
        COMPONENTS = ["earnings", "SSP", "SMP", "SPP", "holiday_pay"]
        applicable_income = add(person, period, COMPONENTS)
        amount = parameters(period).taxes.NI.class_1.rates.calc(applicable_income)
        payable_amount = amount * not_(person("is_SP_age", period.this_year))
        return payable_amount

class NI_class_2(Variable):
    value_type = float
    entity = Person
    label = u'National Insurance (Class 2)'
    definition_period = WEEK
    reference = u'https://www.gov.uk/national-insurance'

    def formula(person, period, parameters):
        class_2 = parameters(period).taxes.NI.class_2
        over_threshold = person("profit", period.this_year) >= class_2.small_earnings_exception
        amount = class_2.flat_rate * over_threshold
        payable_amount = amount * not_(person("is_SP_age", period.this_year))
        return payable_amount

class NI_class_4(Variable):
    value_type = float
    entity = Person
    label = u'National Insurance (Class 4)'
    definition_period = YEAR
    reference = u'https://www.gov.uk/national-insurance'

    def formula(person, period, parameters):
        applicable_income = person("profit", period)
        amount = parameters(period).taxes.NI.class_4.rates.calc(applicable_income)
        payable_amount = amount * not_(person("is_SP_age", period.this_year))
        return payable_amount

class NI(Variable):
    value_type = float
    entity = Person
    label = u'National Insurance total liability'
    definition_period = YEAR
    reference = u'https://www.gov.uk/national-insurance'

    def formula(person, period, parameters):
        return person("NI_class_1", period) + person("NI_class_2", period) + person("NI_class_4", period)
