from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_business_rates_reliefs(Variable):
    value_type = float
    entity = Firm
    label = "Business rates reliefs of the firm"
    documentation = (
        "Total business rates reliefs and exemptions of the firm. "
        "England: empty property, charitable, small business, retail "
        "hospitality and leisure, and pubs and live music venues reliefs; "
        "transitional relief, Supporting Small Business relief, rural rate "
        "relief, improvement relief and local discretionary reliefs are not "
        "modelled. "
        "Wales: small business rates relief only, 100% at or below £6,000 "
        "tapering to 0% at £12,000, for an occupied property of a firm with "
        "at most two properties (the limit is per local authority, applied "
        "here to the firm). Not modelled in Wales: the childcare and post "
        "office rules, charitable and empty property relief, retail and "
        "hospitality reliefs and transitional relief. "
        "Scotland: Small Business Bonus Scheme single-entry relief only, "
        "100% at or below £12,000, tapering to 25% at £15,000 and to 0% at "
        "£20,000, for an occupied property of a firm with one property. Not "
        "modelled in Scotland: SBBS for several properties (cumulative "
        "rateable value up to £35,000), its excluded property uses, "
        "charitable, empty property, retail hospitality and leisure, and "
        "transitional reliefs."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA",
        "https://businesswales.gov.wales/non-domestic-rates-small-business-rates-relief",
        "https://www.gov.scot/publications/local-government-finance-circular-7-2026-non-domestic-rates-relief-guidance/pages/non-domestic-rates-relief-information-for-scottish-local-authorities/",
    ]

    def formula(firm, period, parameters):
        br = parameters(period).gov.hmrc.business_rates
        region = firm("firm_region", period)
        regions = region.possible_values
        is_wales = region == regions.WALES
        is_scotland = region == regions.SCOTLAND

        england = add(
            firm,
            period,
            [
                "firm_empty_property_rates_exemption",
                "firm_charitable_rate_relief",
                "firm_small_business_rate_relief",
                "firm_retail_hospitality_leisure_rate_relief",
                "firm_pubs_and_live_music_venues_rate_relief",
            ],
        )

        gross = firm("firm_gross_business_rates", period)
        rateable_value = firm("firm_rateable_value", period)
        n_properties = firm("firm_n_properties", period)
        occupied = firm("firm_property_occupied", period)

        # Wales small business rates relief
        w = br.wales.small_business
        wales_share = clip(
            (w.taper_end_threshold - rateable_value)
            / (w.taper_end_threshold - w.full_relief_threshold),
            0,
            1,
        )
        wales_eligible = occupied & (n_properties <= w.max_properties)
        wales = where(wales_eligible, gross * wales_share, 0)

        # Scotland Small Business Bonus Scheme, single entry
        s = br.scotland.small_business_bonus
        upper_share = s.middle_relief_rate + (1 - s.middle_relief_rate) * clip(
            (s.middle_threshold - rateable_value)
            / (s.middle_threshold - s.full_relief_threshold),
            0,
            1,
        )
        lower_share = s.middle_relief_rate * clip(
            (s.taper_end_threshold - rateable_value)
            / (s.taper_end_threshold - s.middle_threshold),
            0,
            1,
        )
        scotland_share = where(
            rateable_value <= s.middle_threshold, upper_share, lower_share
        )
        scotland_eligible = occupied & (n_properties == 1)
        scotland = where(scotland_eligible, gross * scotland_share, 0)

        return select([is_wales, is_scotland], [wales, scotland], default=england)
