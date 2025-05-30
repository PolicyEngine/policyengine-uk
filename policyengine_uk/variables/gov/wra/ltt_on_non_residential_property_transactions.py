from policyengine_uk.model_api import *


class ltt_on_non_residential_property_transactions(Variable):
    label = "LTT on non-residential property transactions"
    documentation = (
        "Land Transaction Tax charge on non-residential property transactions"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        ltt = parameters(period).gov.wra.land_transaction_tax
        price = household("non_residential_property_purchased", period)
        non_residential_purchase_tax = ltt.non_residential.calc(price)
        return household("ltt_liable", period) * non_residential_purchase_tax
