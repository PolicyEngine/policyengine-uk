from policyengine_uk.model_api import *


class ltt_on_residential_property_rent(Variable):
    label = "LTT on residential property rent"
    documentation = (
        "Land Transaction Tax charge on residential property rental agreements. "
        "No tax is chargeable on residential lease rent, so this is zero under "
        "current law."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/anaw/2017/1/schedule/6/paragraph/27"

    def formula(household, period, parameters):
        ltt = parameters(period).gov.wra.land_transaction_tax
        cumulative_rent = household("cumulative_residential_rent", period)
        rent = household("rent", period)
        ltt_on_cumulative_rent = ltt.rent.calc(cumulative_rent)
        ltt_on_total_rent = ltt.rent.calc(cumulative_rent + rent)
        charge = ltt_on_total_rent - ltt_on_cumulative_rent
        return where(ltt.residential_lease_rent_exempt, 0, charge)
