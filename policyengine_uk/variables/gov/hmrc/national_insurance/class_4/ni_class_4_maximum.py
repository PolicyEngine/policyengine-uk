from policyengine_uk.model_api import *


class ni_class_4_maximum(Variable):
    label = "NI Class 4 maximum liability"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2001/1004/regulation/100"

    def formula(person, period, parameters):
        ni = parameters(period).gov.hmrc.national_insurance
        upl = ni.class_4.thresholds.upper_profits_limit
        lpl = ni.class_4.thresholds.lower_profits_limit
        step_1 = upl - lpl
        main_rate = ni.class_4.rates.main
        add_rate = ni.class_4.rates.additional
        step_2 = step_1 * main_rate
        step_3 = step_2 + 53 * ni.class_2.flat_rate
        class_2_contributions = person("ni_class_2", period)
        primary_class_1_contributions = person(
            "ni_class_1_employee_primary", period
        )
        step_4 = step_3 - class_2_contributions - primary_class_1_contributions
        class_4_main_contributions = person("ni_class_4_main", period)
        other_aggregate_contributions = (
            primary_class_1_contributions
            + class_2_contributions
            + class_4_main_contributions
        )
        case_1 = (step_4 >= 0) & (step_4 > other_aggregate_contributions)
        case_2 = (step_4 >= 0) & (step_4 <= other_aggregate_contributions)
        case_3 = step_4 < 0
        step_5 = step_4 * 100 / 9
        profits = person("self_employment_income", period)
        step_6 = lpl - min_(upl, profits)
        step_7 = max_(0, step_6 - step_5)
        step_8 = step_7 * add_rate
        step_9 = max_(0, profits - upl)

        return select(
            [
                case_1,
                case_2 | case_3,
            ],
            [step_4, step_4 + step_8 + step_9],
        )
