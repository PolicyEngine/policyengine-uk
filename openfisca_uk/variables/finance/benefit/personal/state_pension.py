from openfisca_uk.model_api import *


class state_pension_age(Variable):
    value_type = float
    entity = Person
    label = "State Pension age for this person"
    definition_period = YEAR
    unit = "year"

    def formula(person, period, parameters):
        SP = parameters(period).benefit.state_pension
        return where(person("is_male", period), SP.male_age, SP.female_age)


class is_SP_age(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is State Pension Age"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        threshold = person("state_pension_age", period)
        return age >= threshold


class triple_lock_uprating(Variable):
    value_type = float
    entity = Person
    label = "Triple lock relative increase"
    documentation = (
        "A government commitment, rather than a legislative requirement"
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        uprating = parameters(period).uprating
        uprating_ly = parameters(period.last_year).uprating
        cpi_growth = uprating.CPI / uprating_ly.CPI
        earnings_growth = uprating.earnings / uprating_ly.earnings
        return max(
            parameters(period).benefit.state_pension.triple_lock_minimum,
            cpi_growth,
            earnings_growth,
        )


class state_pension(Variable):
    value_type = float
    entity = Person
    label = "Income from the State Pension"
    definition_period = YEAR
    unit = "currency-GBP"
    documentation = "Gross State Pension payments"
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("state_pension_reported", period)


class state_pension_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported income from the State Pension"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula_2015(person, period, parameters):
        sp_ly = person("state_pension_reported", period.last_year)
        return sp_ly * person("triple_lock_uprating", period)
