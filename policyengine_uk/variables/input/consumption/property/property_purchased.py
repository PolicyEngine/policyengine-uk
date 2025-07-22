from policyengine_uk.model_api import *


class property_purchased(Variable):
    label = "All property bought this year"
    documentation = "Whether all property wealth was bought this year"
    entity = Household
    definition_period = YEAR
    value_type = bool
    default_value = True
