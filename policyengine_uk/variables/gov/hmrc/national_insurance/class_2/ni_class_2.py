from policyengine_uk.model_api import *


class ni_class_2(Variable):
    value_type = float
    entity = Person
    label = "NI Class 2 contributions"
    definition_period = YEAR
    reference = "Social Security and Benefits Act 1992 s. 11"
    unit = GBP
    defined_for = "ni_liable"
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/11"

    def formula(person, period, parameters):
        class_2 = parameters(period).gov.hmrc.national_insurance.class_2
        profits = person("self_employment_income", period)
        over_threshold = profits >= class_2.small_profits_threshold
        return over_threshold * class_2.flat_rate * WEEKS_IN_YEAR
