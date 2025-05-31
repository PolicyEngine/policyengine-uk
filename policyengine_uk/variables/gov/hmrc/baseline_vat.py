from policyengine_uk.model_api import *


class baseline_vat(Variable):
    label = "baseline VAT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        full_rate_consumption = household("full_rate_vat_consumption", period)
        reduced_rate_consumption = household(
            "reduced_rate_vat_consumption", period
        )
        p = parameters(period).baseline.gov
        vat = p.hmrc.vat
        microdata_vat_coverage = p.simulation.microdata_vat_coverage
        return (
            full_rate_consumption * vat.standard_rate
            + reduced_rate_consumption * vat.reduced_rate
        ) / microdata_vat_coverage
