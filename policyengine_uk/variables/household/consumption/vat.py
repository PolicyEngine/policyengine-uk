from policyengine_uk.model_api import *


class full_rate_vat_consumption(Variable):
    label = "consumption of VAT full-rated goods and services"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        # If unknown, assume half of consumption is VAT full-rated.
        return household("consumption", period) * 0.5


class reduced_rate_vat_consumption(Variable):
    label = "consumption of VAT reduced-rated goods and services"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        vat = parameters(period).gov.hmrc.vat
        consumption = household("consumption", period)
        return consumption * vat.reduced_rate_share
