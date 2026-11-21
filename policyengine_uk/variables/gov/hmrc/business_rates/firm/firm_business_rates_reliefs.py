from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_business_rates_reliefs(Variable):
    value_type = float
    entity = Firm
    label = "Business rates reliefs of the firm"
    documentation = (
        "Total business rates reliefs and exemptions of the firm in England. "
        "Transitional relief, Supporting Small Business relief, rural rate "
        "relief, improvement relief and local discretionary reliefs are not "
        "modelled."
    )
    definition_period = YEAR
    unit = GBP
    adds = [
        "firm_empty_property_rates_exemption",
        "firm_charitable_rate_relief",
        "firm_small_business_rate_relief",
        "firm_retail_hospitality_leisure_rate_relief",
        "firm_pubs_and_live_music_venues_rate_relief",
    ]
