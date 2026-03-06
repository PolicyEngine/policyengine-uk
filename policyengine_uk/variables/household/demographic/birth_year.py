from policyengine_uk.model_api import *


class birth_year(Variable):
    value_type = int
    entity = Person
    label = "The birth year of the person"
    definition_period = YEAR

    def formula(person, period, parameters):
        return period.start.year - person("age", period)
