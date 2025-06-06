from policyengine_uk.model_api import *


class lbtt_on_transactions(Variable):
    label = "LBTT on property transactions"
    documentation = "Land and Buildings Transaction Tax on property transfers"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = [
        "lbtt_on_residential_property_transactions",
        "lbtt_on_non_residential_property_transactions",
    ]
