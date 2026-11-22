from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_small_business_rate_relief(Variable):
    value_type = float
    entity = Firm
    label = "Small business rate relief of the firm"
    documentation = (
        "Small business rate relief in England: 100% of gross rates at or "
        "below the full relief threshold (£12,000), tapering linearly to 0% "
        "at the taper end (£15,000). From 2027-28 to 2028-29 qualifying "
        "retail, hospitality and leisure properties use £18,000 and £21,000. "
        "Only for occupied property of a firm with one property, and not for "
        "a charity, which gets charitable relief instead. Not modelled: "
        "relief kept on the main property when the other properties are each "
        "under £2,900 and in total under £20,000 (£28,000 in London), the "
        "grace period after taking on a second property, the exclusion "
        "of vape shops, and the rounding of the taper factor to three "
        "decimal places in SI 2017/102 art 3(5), which can withhold a few "
        "pounds of relief just below the taper end."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA",
        "https://www.gov.uk/apply-for-business-rate-relief/small-business-rate-relief",
    ]
    defined_for = "firm_property_occupied"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.business_rates.reliefs.small_business
        gross = firm("firm_gross_business_rates", period)
        rateable_value = firm("firm_rateable_value", period)
        is_rhl = firm("firm_is_rhl_property", period)
        full_threshold = where(
            is_rhl, p.rhl_full_relief_threshold, p.full_relief_threshold
        )
        taper_end = where(is_rhl, p.rhl_taper_end_threshold, p.taper_end_threshold)
        share = clip((taper_end - rateable_value) / (taper_end - full_threshold), 0, 1)
        eligible = (firm("firm_n_properties", period) == 1) & ~firm(
            "firm_is_charity", period
        )
        return where(eligible, gross * share, 0)
