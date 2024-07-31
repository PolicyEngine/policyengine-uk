from policyengine_uk.model_api import *


class other_excluded_consumption(Variable):
    label = "other consumption excluded from other categories"
    documentation = "Other consumption excluding mortgage interest, personal care and childcare consumption."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
