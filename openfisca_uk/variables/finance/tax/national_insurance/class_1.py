from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class NI_exempt(Variable):
    value_type = bool
    entity = Person
    label = u"Whether is exempt from National Insurance"
    definition_period = YEAR
    reference = "Social Security Contributions and Benefits Act 1992 s. 6"

    def formula(person, period, parameters):
        return not_(person("over_16", period)) + person("is_SP_age", period)


class employee_NI_class_1(Variable):
    value_type = float
    entity = Person
    label = u"Employee Class 1 Contributions for National Insurance"
    definition_period = YEAR
    reference = "Social Security Contributions and Benefits Act 1992 s. 8"

    def formula(person, period, parameters):
        class_1 = parameters(period).tax.national_insurance.class_1
        earnings = person("employment_income", period)
        main_earnings = amount_between(
            earnings,
            class_1.thresholds.primary_threshold * WEEKS_IN_YEAR,
            class_1.thresholds.upper_earnings_limit * WEEKS_IN_YEAR,
        )
        add_earnings = amount_over(
            earnings, class_1.thresholds.upper_earnings_limit * WEEKS_IN_YEAR
        )
        charge = (
            class_1.rates.employee.main * main_earnings
            + add_earnings * class_1.rates.employee.additional
        )
        return charge


class employer_NI_class_1(Variable):
    value_type = float
    entity = Person
    label = u"Employer Class 1 Contributions for National Insurance"
    definition_period = YEAR
    reference = "Social Security Contributions and Benefits Act 1992 s. 8"

    def formula(person, period, parameters):
        class_1 = parameters(period).tax.national_insurance.class_1
        earnings = person("employment_income", period)
        main_earnings = amount_over(
            earnings,
            class_1.thresholds.secondary_threshold * WEEKS_IN_YEAR,
        )
        charge = class_1.rates.employer * main_earnings
        return charge


class employer_NI(Variable):
    value_type = float
    entity = Person
    label = u"Employer contributions to National Insurance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("employer_NI_class_1", period)


class total_NI(Variable):
    value_type = float
    entity = Person
    label = u"NI (total)"
    definition_period = YEAR

    def formula(person, period, parameters):
        COMPONENTS = ["employer_NI", "national_insurance"]
        return add(person, period, COMPONENTS)
