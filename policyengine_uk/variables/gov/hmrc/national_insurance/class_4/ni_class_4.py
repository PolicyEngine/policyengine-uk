from policyengine_uk.model_api import *


class ni_class_4(Variable):
    value_type = float
    entity = Person
    label = "NI Class 4 main contributions"
    definition_period = YEAR
    unit = GBP
    defined_for = "ni_liable"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.national_insurance.class_4
        self_employment_income = person("self_employment_income", period)
        employee_ni = person("ni_class_1_employee", period)
        profits = self_employment_income - employee_ni
        add_rate_income = max_(
            profits - p.thresholds.upper_profits_limit,
            0,
        )
        main_rate_income = (
            max_(
                profits - p.thresholds.lower_profits_limit,
                0,
            )
            - add_rate_income
        )
        pre_maximum_amount = (
            main_rate_income * p.rates.main
            + add_rate_income * p.rates.additional
        )
        maximum_amount = person("ni_class_4_maximum", period)
        return max_(
            min_(pre_maximum_amount, maximum_amount),
            0,
        )
