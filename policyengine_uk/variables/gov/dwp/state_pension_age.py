from policyengine_uk.model_api import *


class state_pension_age(Variable):
    value_type = float
    entity = Person
    label = "State Pension age for this person"
    definition_period = YEAR
    unit = "year"

    def formula(person, period, parameters):
        SP = parameters(period).gov.dwp.state_pension
        return where(person("is_male", period), SP.age.male, SP.age.female)
