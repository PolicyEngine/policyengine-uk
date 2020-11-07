from openfisca_core.model_api import *
from openfisca_uk.entities import *


class JSA_contrib(Variable):
    value_type = float
    entity = Person
    label = u"Amount of JSA (contribution-based) per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        is_eligible = person("JSA_contrib_reported", period) > 0
        is_lower_age = person("is_adult", period) * person("age", period) < 25
        is_higher_age = (
            person("is_adult", period) * person("age", period) >= 25
        )
        base_amount = is_eligible * (
            is_lower_age * parameters(period).benefits.JSA.contrib.amount_18_24
            + is_higher_age
            * parameters(period).benefits.JSA.contrib.amount_over_25
        )
        earnings_over_threshold = max_(
            0,
            person("taxed_means_tested_bonus", period)
            + person("untaxed_means_tested_bonus", period)
            + person("employee_earnings", period)
            + person("self_employed_earnings", period)
            - parameters(period).benefits.JSA.contrib.earn_disregard,
        )
        pension_over_threshold = max_(
            0,
            person("pension_income", period)
            - parameters(period).benefits.JSA.contrib.pension_disregard,
        )
        means_tested_amount = max_(
            0, base_amount - earnings_over_threshold - pension_over_threshold
        )
        return means_tested_amount


class ESA_contrib(Variable):
    value_type = float
    entity = Person
    label = u"Amount of ESA (contribution-based) per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("ESA_income_reported", period)


class DLA(Variable):
    value_type = float
    entity = Person
    label = u"Amount of Disability Living Allowance per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("DLA_SC_reported", period) + person(
            "DLA_M_reported", period
        )
