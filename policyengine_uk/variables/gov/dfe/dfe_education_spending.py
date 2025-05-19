from policyengine_uk.model_api import *


class dfe_education_spending(Variable):
    label = "state education spending"
    documentation = "Total state education spending for this person."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
