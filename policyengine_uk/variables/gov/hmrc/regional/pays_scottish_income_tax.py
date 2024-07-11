from policyengine_uk.model_api import *


class pays_scottish_income_tax(Variable):
    value_type = bool
    entity = Person
    label = "Whether the individual pays Scottish Income Tax rates"
    definition_period = YEAR

    def formula(person, period, parameters):
        country = person.household("country", period)
        countries = country.possible_values
        return person.household("country", period) == countries.SCOTLAND
