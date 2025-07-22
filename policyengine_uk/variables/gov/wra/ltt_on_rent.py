from policyengine_uk.model_api import *


class ltt_on_rent(Variable):
    label = "LTT on property rental"
    documentation = "Land Transaction Tax on property rental agreements"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        LTT_RENT_VARIABLES = [
            "ltt_on_residential_property_rent",
            "ltt_on_non_residential_property_rent",
        ]
        return add(household, period, LTT_RENT_VARIABLES)
