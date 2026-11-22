from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_business_rates_multiplier(Variable):
    value_type = float
    entity = Firm
    label = "Business rates multiplier for the firm's property"
    documentation = (
        "The non-domestic rating multiplier, in pounds per pound of rateable "
        "value, for the firm's property, chosen by firm_region. "
        "England: a small business multiplier applies below the small "
        "business threshold (£51,000), the standard one from there, and from "
        "2026-27 the high-value multiplier at £500,000 or more. From 2026-27 "
        "qualifying retail, hospitality and leisure (RHL) properties below "
        "£500,000 pay the lower RHL multipliers. The small multiplier is "
        "chosen by rateable value alone; the 1p Transitional Relief "
        "Supplement for 2026-27 is not modelled. "
        "Wales: one multiplier to 2025-26. From 2026-27 the retail "
        "multiplier for shops, kiosks, pharmacies and post offices below "
        "£51,000 (firm_is_wales_retail_property), the higher multiplier "
        "above £100,000 unless the property has one of the 19 excluded "
        "public-service descriptions "
        "(firm_is_wales_higher_multiplier_excluded), and the standard "
        "multiplier otherwise (WSI 2025/1163 regs 3 and 4). "
        "Scotland: the basic property rate, plus the intermediate property "
        "supplement above £51,000 up to £100,000, or the higher property "
        "supplement above £100,000. The firm's rateable value is treated as "
        "one property."
    )
    definition_period = YEAR
    unit = "/1"
    reference = [
        "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA",
        "https://www.gov.uk/government/publications/52025-confirmation-of-budget-package-and-the-non-domestic-rating-multipliers-for-20262027/52025-confirmation-of-budget-package-and-the-non-domestic-rating-multipliers-for-20262027",
        "https://businesswales.gov.wales/non-domestic-rates-multipliers",
        "https://www.legislation.gov.uk/wsi/2025/1163/made",
        "https://www.legislation.gov.uk/ssi/2026/68/made",
    ]

    def formula(firm, period, parameters):
        br = parameters(period).gov.hmrc.business_rates
        rateable_value = firm("firm_rateable_value", period)
        region = firm("firm_region", period)
        regions = region.possible_values

        # England
        p = br.multipliers
        is_rhl = firm("firm_is_rhl_property", period)
        is_small = rateable_value < p.small_business_threshold
        is_high_value = rateable_value >= p.high_value_threshold
        small = where(is_rhl, p.small_business_rhl, p.small_business)
        standard = where(is_rhl, p.standard_rhl, p.standard)
        england = select(
            [is_high_value, is_small],
            [p.high_value, small],
            default=standard,
        )

        # Wales
        w = br.wales.multipliers
        is_wales_retail = firm("firm_is_wales_retail_property", period) & (
            rateable_value < w.retail_threshold
        )
        is_wales_higher = (rateable_value > w.higher_threshold) & ~firm(
            "firm_is_wales_higher_multiplier_excluded", period
        )
        wales = select(
            [is_wales_retail, is_wales_higher],
            [w.retail, w.higher],
            default=w.standard,
        )

        # Scotland
        s = br.scotland.poundage
        supplement = select(
            [
                rateable_value > s.higher_threshold,
                rateable_value > s.intermediate_threshold,
            ],
            [s.higher_supplement, s.intermediate_supplement],
            default=0,
        )
        scotland = s.basic + supplement

        return select(
            [region == regions.WALES, region == regions.SCOTLAND],
            [wales, scotland],
            default=england,
        )
