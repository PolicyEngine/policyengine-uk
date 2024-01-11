from policyengine_uk.model_api import *


class ni_class_1_employee_additional(Variable):
    label = "NI Class 1 employee-side additional contributions"
    entity = Person
    definition_period = MONTH
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/8"

    def formula(person, period, parameters):
        income = person("ni_class_1_income", period)
        parameters = parameters(period).gov.hmrc.national_insurance.class_1
        upper_earnings_limit = (
            parameters.thresholds.upper_earnings_limit
            * WEEKS_IN_YEAR
            / MONTHS_IN_YEAR
        )
        upper_earnings_limit_income = max_(income - upper_earnings_limit, 0)
        return (
            parameters.rates.employee.additional * upper_earnings_limit_income
        )
