from policyengine_uk.model_api import *


class ltt_liable(Variable):
    label = "Liable for Land Transaction Tax"
    documentation = (
        "Whether the household is liable to pay the Wales Land Transaction Tax"
    )
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period):
        country = household("country", period)
        return country == country.possible_values.WALES
