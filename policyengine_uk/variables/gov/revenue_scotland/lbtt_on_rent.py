from policyengine_uk.model_api import *


class lbtt_on_rent(Variable):
    label = "LBTT on property rental"
    documentation = (
        "Land and Buildings Transaction Tax on property rental agreements"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = [
        "lbtt_on_residential_property_rent",
        "lbtt_on_non_residential_property_rent",
    ]
