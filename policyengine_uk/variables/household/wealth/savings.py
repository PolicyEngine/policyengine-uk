from policyengine_uk.model_api import *


class savings(Variable):
    label = "Savings"
    documentation = "Household liquid savings"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
