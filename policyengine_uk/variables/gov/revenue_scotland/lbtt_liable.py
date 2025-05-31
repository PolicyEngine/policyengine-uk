from policyengine_uk.model_api import *


class lbtt_liable(Variable):
    label = "Liable for Land and Buildings Transaction Tax"
    documentation = "Whether the household is liable for Land and Buildings Transaction Tax"
    entity = Household
    definition_period = YEAR
    value_type = bool
    unit = GBP

    def formula(household, period):
        country = household("country", period)
        countries = country.possible_values
        return country == countries.SCOTLAND
