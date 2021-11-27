from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class state_pension_age(Variable):
    value_type = float
    entity = Person
    label = u"State Pension age for this person"
    definition_period = YEAR

    def formula(person, period, parameters):
        SP = parameters(period).benefit.state_pension
        male = person("is_male", period)
        threshold = male * SP.male_age + not_(male) * SP.female_age
        return threshold


class is_SP_age(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is State Pension Age"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        threshold = person("state_pension_age", period)
        over = age >= threshold
        return over


class triple_lock_uprating(Variable):
    value_type = float
    entity = Person
    label = u"Triple lock relative increase"
    documentation = (
        "A government commitment, rather than a legislative requirement"
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        cpi_growth = (
            parameters(period).uprating.CPI
            / parameters(period.last_year).uprating.CPI
        )
        earnings_growth = (
            parameters(period).uprating.earnings
            / parameters(period.last_year).uprating.earnings
        )
        return max(
            parameters(period).benefit.state_pension.triple_lock_minimum,
            cpi_growth,
            earnings_growth,
        )


class state_pension(Variable):
    value_type = float
    entity = Person
    label = u"Income from the State Pension"
    definition_period = YEAR
    unit = "currency-GBP"
    documentation = "Gross State Pension payments"

    def formula(person, period, parameters):
        return person("state_pension_reported", period)


class state_pension_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported income from the State Pension"
    definition_period = YEAR

    def formula_2015(person, period, parameters):
        return person("state_pension_reported", period.last_year) * person(
            "triple_lock_uprating", period
        )
