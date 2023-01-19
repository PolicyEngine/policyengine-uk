from policyengine_uk.model_api import *


class NI_exempt(Variable):
    value_type = bool
    entity = Person
    label = "Exempt from National Insurance"
    documentation = "Whether a person is exempt from National Insurance"
    definition_period = YEAR
    reference = "Social Security Contributions and Benefits Act 1992 s. 6"

    def formula(person, period, parameters):
        return ~person("over_16", period) | person("is_SP_age", period)


class monthly_employee_NI_class_1(Variable):
    value_type = float
    entity = Person
    label = "Monthly employee Class 1 Contributions for National Insurance"
    definition_period = MONTH
    reference = "Social Security Contributions and Benefits Act 1992 s. 8"
    unit = GBP

    def formula(person, period, parameters):
        class_1 = parameters(period).gov.hmrc.national_insurance.class_1
        earnings = (
            person("employment_income", period.this_year) / MONTHS_IN_YEAR
        )
        main_earnings = amount_between(
            earnings,
            class_1.thresholds.primary_threshold
            * WEEKS_IN_YEAR
            / MONTHS_IN_YEAR,
            class_1.thresholds.upper_earnings_limit
            * WEEKS_IN_YEAR
            / MONTHS_IN_YEAR,
        )
        add_earnings = amount_over(
            earnings,
            class_1.thresholds.upper_earnings_limit
            * WEEKS_IN_YEAR
            / MONTHS_IN_YEAR,
        )
        main_charge = class_1.rates.employee.main * main_earnings
        add_charge = class_1.rates.employee.additional * add_earnings
        return main_charge + add_charge


class employee_NI_class_1(Variable):
    label = "Employee NI class 1"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(person, period, parameters):
        total_NI = 0
        for month in period.get_subperiods("month"):
            total_NI += person("monthly_employee_NI_class_1", month)
        return total_NI


class employer_NI_class_1(Variable):
    value_type = float
    entity = Person
    label = "Employer Class 1 Contributions for National Insurance"
    definition_period = YEAR
    reference = "Social Security Contributions and Benefits Act 1992 s. 8"
    unit = GBP

    def formula(person, period, parameters):
        class_1 = parameters(period).gov.hmrc.national_insurance.class_1
        earnings = person("employment_income", period)
        main_earnings = amount_over(
            earnings,
            class_1.thresholds.secondary_threshold * WEEKS_IN_YEAR,
        )
        return class_1.rates.employer * main_earnings


class employer_NI(Variable):
    value_type = float
    entity = Person
    label = "Employer contributions to National Insurance"
    definition_period = YEAR
    unit = GBP

    adds = ["employer_NI_class_1"]


class total_NI(Variable):
    value_type = float
    entity = Person
    label = "National Insurance (total)"
    definition_period = YEAR
    unit = GBP

    adds = ["employer_NI", "national_insurance"]
