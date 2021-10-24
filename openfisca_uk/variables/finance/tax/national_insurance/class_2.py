from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class weekly_NI_class_2(Variable):
    value_type = float
    entity = Person
    label = u"Class 2 Contributions for National Insurance"
    definition_period = YEAR
    reference = "Social Security and Benefits Act 1992 s. 11"

    def formula(person, period, parameters):
        class_2 = parameters(period).tax.national_insurance.class_2
        profits = person("self_employment_income", period)
        over_threshold = profits >= class_2.small_profits_threshold
        charge = over_threshold * class_2.flat_rate * WEEKS_IN_YEAR
        return charge


class NI_class_2(Variable):
    value_type = float
    entity = Person
    label = u"Class 2 Contributions for National Insurance for the year"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("weekly_NI_class_2", period)
