from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_pubs_and_live_music_venues_rate_relief(Variable):
    value_type = float
    entity = Firm
    label = "Pubs and live music venues business rates relief of the firm"
    documentation = (
        "Relief for occupied pubs and live music venues in England: 15% in "
        "2026-27 and 35% in 2027-28 and 2028-29, with venues at rateable "
        "value £1m or more kept at 15%. The model applies it to the bill left "
        "after all other reliefs (the order is an assumption) and applies "
        "the £1m rule, set for live music venues, to pubs as well."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.gov.uk/apply-for-business-rate-relief/pubs-and-live-music-venues-relief",
        "https://www.gov.uk/government/publications/82026-details-of-the-budget-package-and-the-multipliers-for-20272028/82026-details-of-the-budget-package-and-the-multipliers-for-20272028",
    ]
    defined_for = "firm_property_occupied"

    def formula(firm, period, parameters):
        p = parameters(
            period
        ).gov.hmrc.business_rates.reliefs.pubs_and_live_music_venues
        gross = firm("firm_gross_business_rates", period)
        other_reliefs = add(
            firm,
            period,
            [
                "firm_charitable_rate_relief",
                "firm_small_business_rate_relief",
                "firm_retail_hospitality_leisure_rate_relief",
            ],
        )
        remaining = max_(gross - other_reliefs, 0)
        rateable_value = firm("firm_rateable_value", period)
        rate = where(
            rateable_value >= p.large_venue_threshold,
            p.large_venue_rate,
            p.rate,
        )
        is_venue = firm("firm_is_pub_or_live_music_venue", period)
        return where(is_venue, remaining * rate, 0)
