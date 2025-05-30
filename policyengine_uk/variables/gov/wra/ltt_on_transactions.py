from policyengine_uk.model_api import *


class ltt_on_transactions(Variable):
    label = "LTT on property transactions"
    documentation = "Land Transaction Tax on property transfers"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        LTT_TRANSACTION_VARIABLES = [
            "ltt_on_residential_property_transactions",
            "ltt_on_non_residential_property_transactions",
        ]
        return add(household, period, LTT_TRANSACTION_VARIABLES)
