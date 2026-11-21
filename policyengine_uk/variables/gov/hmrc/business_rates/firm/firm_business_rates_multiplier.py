from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_business_rates_multiplier(Variable):
    value_type = float
    entity = Firm
    label = "Business rates multiplier for the firm's property"
    documentation = (
        "The non-domestic rating multiplier, in pounds per pound of rateable "
        "value, for the firm's property in England. A small business "
        "multiplier applies below the small business threshold (£51,000), "
        "the standard one from there, and from 2026-27 the high-value "
        "multiplier at £500,000 or more. From 2026-27 qualifying retail, "
        "hospitality and leisure (RHL) properties below £500,000 pay the "
        "lower RHL multipliers. The firm's rateable value is treated as one "
        "property. The small multiplier is chosen by rateable value alone; "
        "the 1p Transitional Relief Supplement for 2026-27 is not modelled."
    )
    definition_period = YEAR
    unit = "/1"
    reference = [
        "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA",
        "https://www.gov.uk/government/publications/52025-confirmation-of-budget-package-and-the-non-domestic-rating-multipliers-for-20262027/52025-confirmation-of-budget-package-and-the-non-domestic-rating-multipliers-for-20262027",
    ]

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.business_rates.multipliers
        rateable_value = firm("firm_rateable_value", period)
        is_rhl = firm("firm_is_rhl_property", period)
        is_small = rateable_value < p.small_business_threshold
        is_high_value = rateable_value >= p.high_value_threshold
        small = where(is_rhl, p.small_business_rhl, p.small_business)
        standard = where(is_rhl, p.standard_rhl, p.standard)
        return select(
            [is_high_value, is_small],
            [p.high_value, small],
            default=standard,
        )
