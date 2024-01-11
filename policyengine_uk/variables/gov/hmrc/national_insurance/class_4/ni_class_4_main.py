from policyengine_uk.model_api import *


class ni_class_4_main(Variable):
    value_type = float
    entity = Person
    label = "NI Class 4 main contributions"
    definition_period = YEAR
    unit = GBP
    defined_for = "ni_liable"
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/15"

    def formula(person, period, parameters):
        class_4 = parameters(period).gov.hmrc.national_insurance.class_4
        self_employment_income = person("self_employment_income", period)
        employee_NI = person("ni_class_1_employee", period)
        profits = self_employment_income - employee_NI
        add_rate_income = max_(
            profits - class_4.thresholds.upper_profits_limit,
            0,
        )
        main_rate_income = (
            max_(
                profits - class_4.thresholds.lower_profits_limit,
                0,
            )
            - add_rate_income
        )
        return main_rate_income * class_4.rates.main
