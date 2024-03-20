from policyengine_uk.model_api import *


class ni_class_1_employee_primary(Variable):
    label = "NI Class 1 employee-side primary contributions"
    entity = Person
    definition_period = MONTH
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/8"

    def formula(person, period, parameters):
        income = person("ni_class_1_income", period)
        parameters = parameters(period).gov.hmrc.national_insurance.class_1

        # Thresholds are weekly, so multiply by weeks in year and divide by months in year
        primary_threshold = (
            parameters.thresholds.primary_threshold
            * WEEKS_IN_YEAR
            / MONTHS_IN_YEAR
        )
        upper_earnings_limit = (
            parameters.thresholds.upper_earnings_limit
            * WEEKS_IN_YEAR
            / MONTHS_IN_YEAR
        )

        upper_earnings_limit_income = max_(income - upper_earnings_limit, 0)
        primary_threshold_income = (
            max_(income - primary_threshold, 0) - upper_earnings_limit_income
        )

        return parameters.rates.employee.main * primary_threshold_income
