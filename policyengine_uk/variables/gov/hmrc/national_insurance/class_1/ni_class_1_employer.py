from policyengine_uk.model_api import *


class ni_class_1_employer(Variable):
    value_type = float
    entity = Person
    label = "NI Class 1 employer-side contributions"
    definition_period = MONTH
    unit = GBP
    defined_for = "ni_liable"
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/9"

    def formula(person, period, parameters):
        class_1 = parameters(period).gov.hmrc.national_insurance.class_1
        earnings = person("ni_class_1_income", period)
        if not parameters(
            period
        ).gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions:
            earnings = earnings + person(
                "employer_pension_contributions", period
            )
        secondary_threshold = (
            class_1.thresholds.secondary_threshold
            * WEEKS_IN_YEAR
            / MONTHS_IN_YEAR
        )
        main_earnings = max_(
            earnings - secondary_threshold,
            0,
        )
        return class_1.rates.employer * main_earnings
