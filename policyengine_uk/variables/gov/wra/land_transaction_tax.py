from policyengine_uk.model_api import *


class land_transaction_tax(Variable):
    label = "Land Transaction Tax"
    documentation = "Total tax liability for Land Transaction Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        ltt_if_liable = add(
            household, period, ["ltt_on_transactions", "ltt_on_rent"]
        )
        return household("ltt_liable", period) * ltt_if_liable
