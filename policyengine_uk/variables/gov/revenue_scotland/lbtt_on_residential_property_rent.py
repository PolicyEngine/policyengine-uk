from policyengine_uk.model_api import *


class lbtt_on_residential_property_rent(Variable):
    label = "LBTT on residential property rent"
    documentation = (
        "LBTT charge on rental of residential property. Residential leases are "
        "exempt transactions, so this is zero under current law."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/asp/2013/11/schedule/1/paragraph/3"

    def formula(household, period, parameters):
        lbtt = parameters(period).gov.revenue_scotland.lbtt
        cumulative_rent = household("cumulative_residential_rent", period)
        rent = household("rent", period)
        lbtt_cumulative_rent = lbtt.rent.calc(cumulative_rent)
        lbtt_total_rent = lbtt.rent.calc(cumulative_rent + rent)
        charge = lbtt_total_rent - lbtt_cumulative_rent
        return where(lbtt.residential_lease_exempt, 0, charge)
