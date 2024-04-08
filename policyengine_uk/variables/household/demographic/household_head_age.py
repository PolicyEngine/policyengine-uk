from policyengine_uk.model_api import *


class household_head_age(Variable):
    label = "household head age"
    entity = Household
    definition_period = YEAR
    value_type = int
    unit = "year"

    def formula(household, period, parameters):
        person = household.members
        age = person("age", period)
        return household.max(age)
