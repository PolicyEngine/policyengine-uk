from policyengine_uk.model_api import *


class reduced_rate_vat_consumption(Variable):
    label = "consumption of VAT reduced-rated goods and services other than domestic fuel and power"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        # Domestic electricity and gas are taxed from their own bills in
        # domestic_energy_vat, so the domestic fuel and power share of spending
        # comes out of the reduced-rate share here.
        vat = parameters(period).gov.hmrc.vat
        share = max_(vat.reduced_rate_share - vat.domestic_fuel_and_power_share, 0)
        return household("consumption", period) * share
