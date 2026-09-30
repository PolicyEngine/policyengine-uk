from policyengine_uk.model_api import *


class birth_year(Variable):
    value_type = int
    entity = Person
    label = "The birth year of the person"
    documentation = "The calendar year of the person's date_of_birth."
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("date_of_birth", period) // 10000
