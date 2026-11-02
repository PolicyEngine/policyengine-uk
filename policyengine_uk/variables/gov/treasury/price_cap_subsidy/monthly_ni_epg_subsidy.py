from policyengine_uk.model_api import *
from policyengine_uk.utils.energy_price_guarantee import ni_epg_calculation


class monthly_ni_epg_subsidy(Variable):
    label = "Monthly Northern Ireland Energy Price Guarantee consumer relief"
    documentation = (
        "Consumer bill relief, including avoided customer VAT, when supplied "
        "inputs establish that the full published discounts apply. A zero "
        "with ni_epg_subsidy_calculable false is uncomputed. This is not the "
        "VAT-exclusive supplier grant."
    )
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = GBP
    reference = (
        "https://www.uregni.gov.uk/news-centre/energy-price-guarantee-scheme-and-what-it-means-northern-irelands-regulated-energy",
        "https://www.gov.uk/guidance/vat-on-fuel-and-power-notice-70119#the-energy-price-guarantee",
    )

    def formula(household, period, parameters):
        return ni_epg_calculation(household, period, parameters)[0]
