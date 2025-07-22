from policyengine_uk.model_api import *


class land_and_buildings_transaction_tax(Variable):
    label = "Land and Buildings Transaction Tax"
    documentation = "Total tax liability for Scotland's LBTT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        LBTTS = [
            "lbtt_on_transactions",
            "lbtt_on_rent",
        ]
        lbtt_if_liable = add(household, period, LBTTS)
        return household("lbtt_liable", period) * lbtt_if_liable
