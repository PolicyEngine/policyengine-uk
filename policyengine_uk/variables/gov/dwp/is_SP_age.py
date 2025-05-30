from policyengine_uk.model_api import *


class is_SP_age(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is State Pension Age"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        threshold = person("state_pension_age", period)
        return age >= threshold
