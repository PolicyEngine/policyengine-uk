from policyengine_uk.model_api import *


class ni_class_2(Variable):
    value_type = float
    entity = Person
    label = "NI Class 2 contributions"
    definition_period = YEAR
    unit = GBP
    defined_for = "ni_liable"
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/11"

    def formula(person, period, parameters):
        class_2 = parameters(period).gov.hmrc.national_insurance.class_2
        profits = person("self_employment_income", period)
        # Section 11(2) SSCBA 1992. From 2022-23 only profits that exceed the
        # lower profits threshold are liable; profits from the small profits
        # threshold up to it are treated as paid (s.11(5A)-(5B)) and cost
        # nothing. Before then liability started at the small profits
        # threshold. The flat rate is 0 once s.11(2) is omitted in 2024-25.
        liable = where(
            class_2.lower_profits_threshold_applies,
            profits > class_2.lower_profits_threshold,
            profits >= class_2.small_profits_threshold,
        )
        return liable * class_2.flat_rate * WEEKS_IN_YEAR
