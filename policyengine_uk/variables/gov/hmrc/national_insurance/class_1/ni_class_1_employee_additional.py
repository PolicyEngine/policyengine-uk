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
            parameters.employee_scale.components[2].threshold
            * WEEKS_IN_YEAR
            / MONTHS_IN_YEAR
        )
        upper_earnings_limit_income = max_(income - upper_earnings_limit, 0)
        ordinary = (
            parameters.employee_scale.components[2].rate * upper_earnings_limit_income
        )
        directors = parameters.directors.full_year_category_a_2022_23
        if not directors.in_effect:
            return ordinary

        # Match the annual primary component; this is not an interim payroll charge.
        scale = directors.employee_scale
        annual_income = person("ni_class_1_income", period.this_year)
        annual_additional = scale.rates[2] * max_(
            annual_income - scale.thresholds[2], 0
        )
        return where(
            person("is_full_year_category_a_director", period.this_year),
            annual_additional / MONTHS_IN_YEAR,
            ordinary,
        )
