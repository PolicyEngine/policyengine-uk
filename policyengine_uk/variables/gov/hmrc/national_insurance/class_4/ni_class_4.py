from policyengine_uk.model_api import *


class ni_class_4(Variable):
    value_type = float
    entity = Person
    label = "NI Class 4 main contributions"
    definition_period = YEAR
    unit = GBP
    defined_for = "ni_liable"

    def formula(person, period, parameters):
        class_4 = parameters(period).gov.hmrc.national_insurance.class_4
        # Schedule 2 para 2: Class 4 is charged on the full trading profits;
        # Class 1 contributions are not a deduction.
        profits = person("self_employment_income", period)
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
        pre_maximum_amount = (
            main_rate_income * class_4.rates.main
            + add_rate_income * class_4.rates.additional
        )
        maximum_amount = person("ni_class_4_maximum", period)
        # Regulation 100(1): the annual maximum applies only where primary
        # Class 1 (or, before 6 April 2024, Class 2) contributions are also
        # payable for the year.
        includes_class_2 = class_4.annual_maximum.includes_class_2
        maximum_applies = (person("ni_class_1_employee", period) > 0) | np.logical_and(
            includes_class_2, person("ni_class_2", period) > 0
        )
        return max_(
            where(
                maximum_applies,
                min_(pre_maximum_amount, maximum_amount),
                pre_maximum_amount,
            ),
            0,
        )
