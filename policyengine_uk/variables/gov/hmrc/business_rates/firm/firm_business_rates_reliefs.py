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
        "Wales: mandatory charitable relief (80%) and small business rates "
        "relief, 100% at or below £6,000 tapering to 0% at £12,000, for an "
        "occupied property of a firm with at most two properties (the limit "
        "is per local authority, applied here to the firm). Where both apply "
        "the charity calculation is used (LGFA 1988 Schedule 4ZA para 9; "
        "s.43(8B) before April 2024), so a charity gets 80% even where SBRR "
        "would give more. Not modelled in Wales: the childcare and post "
        "office rules, the independent school exclusion from charitable "
        "relief, discretionary top-ups, empty property relief, retail and "
        "hospitality reliefs and transitional relief. "
        "Scotland: mandatory charitable relief (80%) and Small Business Bonus "
        "Scheme single-entry relief, 100% at or below £12,000, tapering to "
        "25% at £15,000 and to 0% at £20,000, for an occupied property of a "
        "firm with one property. SBBS is reduced by any charitable relief, "
        "but not below nil (levying regulations, regulation 3(4)), so a "
        "charity gets the larger of the two. Not modelled in Scotland: SBBS "
        "for several properties (cumulative rateable value up to £35,000), "
        "its excluded property uses, the independent school exclusion from "
        "charitable relief, discretionary top-ups, empty property, retail "
        "hospitality and leisure, and transitional reliefs. "
        "Northern Ireland, from 2023-24: a charity's occupied property is "
        "exempt (Rates (NI) Order 1977 Art 41); small business rate relief "
        "is 50% at a net annual value up to £2,000, 25% up to £5,000 and "
        "20% up to £15,000, for a wholly occupied, non-industrial property "
        "of a firm with at most three properties, to 31 March 2027 (SR "
        "2010/4 reg 3; SR 2026/45); and unoccupied property is charged half "
        "the bill after its first three months empty, and nothing below "
        "£2,000 or for industrial property (Sch 8A; SR 2011/36). The bands "
        "are applied to the firm's aggregate value. Not modelled in "
        "Northern Ireland: industrial and freight derating, sport and "
        "recreation relief, the post office bands and other exclusions "
        "from small business relief, hardship relief, Back in Business, "
        "part-exempt apportionment, the contiguous-hereditaments rule, the "
        "other unoccupied-property exclusions (such as listed buildings and "
        "insolvency) and any exemption of unoccupied charity property, "
        "which is charged like other unoccupied property here."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA",
        "https://www.legislation.gov.uk/ukpga/1988/41/section/43/2023-04-01",
        "https://www.legislation.gov.uk/ukpga/1962/9/section/4",
        "https://www.legislation.gov.uk/ssi/2026/68/regulation/3/made",
        "https://businesswales.gov.wales/non-domestic-rates-small-business-rates-relief",
        "https://www.gov.scot/publications/local-government-finance-circular-7-2026-non-domestic-rates-relief-guidance/pages/non-domestic-rates-relief-information-for-scottish-local-authorities/",
        "https://www.legislation.gov.uk/nisi/1977/2157/article/41",
        "https://www.legislation.gov.uk/nisr/2010/4",
        "https://www.legislation.gov.uk/nisi/1977/2157/schedule/8A",
        "https://www.legislation.gov.uk/nisr/2011/36",
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
        wales_sbrr = where(wales_eligible, gross * wales_share, 0)
        # Where charitable relief and SBRR both apply, the chargeable amount
        # follows the charity calculation (Sch 4ZA para 9; s.43(8B)).
        charitable = firm("firm_charitable_rate_relief", period)
        is_charity = firm("firm_is_charity", period)
        wales = where(is_charity, charitable, wales_sbrr)

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
        scotland_sbbs = where(scotland_eligible, gross * scotland_share, 0)
        # SBBS is reduced by charitable relief but not below nil, so the
        # total is the larger of the two (levying regulations reg 3(4)).
        scotland = max_(scotland_sbbs, charitable)

        # Northern Ireland
        ni = parameters(period).gov.hmrc.business_rates.northern_ireland
        is_ni = firm("firm_rates_in_northern_ireland", period)
        if ni.modelled:
            industrial = firm("firm_is_industrial_property", period)
            sb = ni.small_business
            sbrr_rate = sb.relief_rate.calc(rateable_value, right=True)
            sbrr_eligible = (
                sb.in_effect
                & occupied
                & ~industrial
                & (n_properties <= sb.max_properties)
            )
            sbrr = where(sbrr_eligible, gross * sbrr_rate, 0)
            occupied_relief = where(is_charity, gross, sbrr)
            u = ni.unoccupied
            free_months_this_year = clip(
                u.free_months - firm("firm_months_empty", period), 0, MONTHS_IN_YEAR
            )
            charged = (
                gross
                * u.rate
                * (MONTHS_IN_YEAR - free_months_this_year)
                / MONTHS_IN_YEAR
            )
            exempt = industrial | (rateable_value < u.exempt_nav_threshold)
            unoccupied_relief = where(exempt, gross, gross - charged)
            northern_ireland = where(occupied, occupied_relief, unoccupied_relief)
        else:
            northern_ireland = 0
        return select(
            [is_wales, is_scotland, is_ni],
            [wales, scotland, northern_ireland],
            default=england,
        )
