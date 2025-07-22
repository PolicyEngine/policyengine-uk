from policyengine_uk.model_api import *


class lbtt_on_residential_property_rent(Variable):
    label = "LBTT on residential property rent"
    documentation = "LBTT charge on rental of residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        lbtt = parameters(period).gov.revenue_scotland.lbtt
        cumulative_rent = household("cumulative_residential_rent", period)
        rent = household("rent", period)
        lbtt_cumulative_rent = lbtt.rent.calc(cumulative_rent)
        lbtt_total_rent = lbtt.rent.calc(cumulative_rent + rent)
        return lbtt_total_rent - lbtt_cumulative_rent
