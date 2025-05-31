from policyengine_uk.model_api import *


class vat(Variable):
    label = "VAT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        full_rate_consumption = household("full_rate_vat_consumption", period)
        reduced_rate_consumption = household(
            "reduced_rate_vat_consumption", period
        )
        p = parameters(period).gov
        raw_vat = (
            full_rate_consumption * p.hmrc.vat.standard_rate
            + reduced_rate_consumption * p.hmrc.vat.reduced_rate
        )
        return raw_vat / p.simulation.microdata_vat_coverage
