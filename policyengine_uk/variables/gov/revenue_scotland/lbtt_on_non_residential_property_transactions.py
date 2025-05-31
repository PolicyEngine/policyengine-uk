from policyengine_uk.model_api import *


class lbtt_on_non_residential_property_transactions(Variable):
    label = "LBTT on non-residential property transactions"
    documentation = "LBTT charge from purchase of non-residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        lbtt = parameters(period).gov.revenue_scotland.lbtt
        price = household("non_residential_property_purchased", period)
        return lbtt.non_residential.calc(price)
