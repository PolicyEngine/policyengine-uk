from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class NI_class_4_maximum(Variable):
    value_type = float
    entity = Person
    label = u"label"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2001/1004/regulation/100"

    def formula(person, period, parameters):
        NI = parameters(period).tax.national_insurance
        class_4 = NI.class_4
        LPL = class_4.thresholds.lower_profits_limit
        UPL = class_4.thresholds.upper_profits_limit
        add_rate = class_4.rates.additional
        step_1_result = UPL - LPL
        step_2_result = step_1_result * class_4.rates.main
        step_3_result = step_2_result + NI.class_2.flat_rate * 53
        step_4_result = step_3_result - add(
            person, period, ["employee_NI_class_1", "NI_class_2"]
        )
        NI_paid = add(
            person,
            period,
            ["employee_NI_class_1", "NI_class_2", "NI_class_4_uncapped"],
        )
        profits = person("self_employment_income", period)
        case = [
            step_4_result > NI_paid,
            step_4_result > 0,
            step_4_result < 0,
        ]
        step_4_result = select(
            case,
            [
                person("NI_class_4_uncapped", period),
                step_2_result,  # equivalently
                0,
            ],
        )
        step_5_result = step_4_result * 100 / 9
        step_6_result = min_(UPL, profits) - LPL
        step_7_result = max_(0, step_6_result - step_5_result)
        step_8_result = step_7_result * add_rate
        step_9_result = max_(0, profits - UPL) * add_rate
        steps_4_8_9 = sum((step_4_result, step_8_result, step_9_result))
        return select(
            case,
            [
                step_4_result,
                steps_4_8_9,
                steps_4_8_9,
            ],
        )


class NI_class_4(Variable):
    value_type = float
    entity = Person
    label = u"Class 4 Contributions for National Insurance for the year"
    definition_period = YEAR
    reference = "Social Security and Benefits Act 1992 s. 15"

    def formula(person, period, parameters):
        class_4 = parameters(period).tax.national_insurance.class_4
        profits = person("self_employment_income", period) - person(
            "employee_NI", period
        )
        main_amount = amount_between(
            profits,
            class_4.thresholds.lower_profits_limit,
            class_4.thresholds.upper_profits_limit,
        )
        add_amount = amount_over(
            profits, class_4.thresholds.upper_profits_limit
        )
        charge = (
            main_amount * class_4.rates.main
            + add_amount * class_4.rates.additional
        )
        return charge


class employee_NI(Variable):
    value_type = float
    entity = Person
    label = u"label"
    definition_period = YEAR
    reference = ""

    def formula(person, period, parameters):
        return person("employee_NI_class_1", period)


class self_employed_NI(Variable):
    value_type = float
    entity = Person
    label = u"label"
    definition_period = YEAR
    reference = ""

    def formula(person, period, parameters):
        return add(person, period, ("NI_class_2", "NI_class_4"))


class national_insurance(Variable):
    value_type = float
    entity = Person
    label = u"National Insurance"
    definition_period = YEAR
    reference = "Social Security and Benefits Act 1992 s. 1(2)"

    def formula(person, period, parameters):
        CLASSES = ["employee_NI", "self_employed_NI"]
        total = add(person, period, CLASSES)
        return total
