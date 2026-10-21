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
            parameters.employee_scale.components[1].threshold
            * WEEKS_IN_YEAR
            / MONTHS_IN_YEAR
        )
        upper_earnings_limit = (
            parameters.employee_scale.components[2].threshold
            * WEEKS_IN_YEAR
            / MONTHS_IN_YEAR
        )

        upper_earnings_limit_income = max_(income - upper_earnings_limit, 0)
        primary_threshold_income = (
            max_(income - primary_threshold, 0) - upper_earnings_limit_income
        )

        ordinary = (
            parameters.employee_scale.components[1].rate * primary_threshold_income
        )
        directors = parameters.directors.full_year_category_a_2022_23
        if not directors.in_effect:
            return ordinary

        # These are annual earnings-period amounts, allocated evenly to model months.
        scale = directors.employee_scale
        annual_income = person("ni_class_1_income", period.this_year)
        annual_primary = scale.rates[1] * min_(
            max_(annual_income - scale.thresholds[1], 0),
            scale.thresholds[2] - scale.thresholds[1],
        )
        return where(
            person("is_full_year_category_a_director", period.this_year),
            annual_primary / MONTHS_IN_YEAR,
            ordinary,
        )
