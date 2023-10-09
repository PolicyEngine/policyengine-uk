from policyengine_uk.model_api import *


class NI_class_4(Variable):
    value_type = float
    entity = Person
    label = "Class 4 Contributions for National Insurance for the year"
    definition_period = YEAR
    reference = "Social Security and Benefits Act 1992 s. 15"
    unit = GBP

    def formula(person, period, parameters):
        class_4 = parameters(period).gov.hmrc.national_insurance.class_4
        self_employment_income = person("self_employment_income", period)
        employee_NI = person("employee_NI", period)
        profits = self_employment_income - employee_NI
        main_amount = amount_between(
            profits,
            class_4.thresholds.lower_profits_limit,
            class_4.thresholds.upper_profits_limit,
        )
        add_amount = max_(profits - class_4.thresholds.upper_profits_limit, 0)
        main_charge = main_amount * class_4.rates.main
        add_charge = add_amount * class_4.rates.additional
        return main_charge + add_charge


class employee_NI(Variable):
    value_type = float
    entity = Person
    label = "employee-side National Insurance"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        exempt = person("NI_exempt", period)
        return person("employee_NI_class_1", period) * ~exempt


class self_employed_NI(Variable):
    value_type = float
    entity = Person
    label = "self-employed National Insurance"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        exempt = person("NI_exempt", period)
        return add(person, period, ("NI_class_2", "NI_class_4")) * ~exempt


class national_insurance(Variable):
    value_type = float
    entity = Person
    label = "National Insurance"
    documentation = "Total National Insurance contributions"
    definition_period = YEAR
    unit = GBP
    reference = "Social Security and Benefits Act 1992 s. 1(2)"
    adds = [
        "employee_NI",
        "self_employed_NI",
    ]
