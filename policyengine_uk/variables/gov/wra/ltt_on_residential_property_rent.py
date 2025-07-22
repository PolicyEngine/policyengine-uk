from policyengine_uk.model_api import *


class ltt_on_residential_property_rent(Variable):
    label = "LTT on residential property rent"
    documentation = (
        "Land Transaction Tax charge on residential property rental agreements"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        ltt = parameters(period).gov.wra.land_transaction_tax
        cumulative_rent = household("cumulative_residential_rent", period)
        rent = household("rent", period)
        ltt_on_cumulative_rent = ltt.rent.calc(cumulative_rent)
        ltt_on_total_rent = ltt.rent.calc(cumulative_rent + rent)
        return ltt_on_total_rent - ltt_on_cumulative_rent
