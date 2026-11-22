from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_small_business_rate_relief(Variable):
    value_type = float
    entity = Firm
    label = "Small business rate relief of the firm"
    documentation = (
        "Small business rate relief in England. Sch 4ZA para 4(1) to the "
        "Local Government Finance Act 1988 divides the gross bill by E. Up to "
        "the full relief threshold (£12,000) the model gives 100% relief "
        "(the law sets E at 5,000,000, which leaves a bill of gross / "
        "5,000,000, under a penny a year). Above it and up to the taper end "
        "(£15,000), E = 3,000 / (rateable value - 12,000), rounded to three "
        "decimal places (SI 2023/1250 reg 3), and relief is gross - gross / "
        "E. The rounding withholds all relief just below the taper end (E "
        "rounds to 1.000 at £14,999). From 2027-28 to 2028-29 qualifying "
        "retail, hospitality and leisure properties use £18,000 and £21,000, "
        "with E = 3,000 / (rateable value - 18,000) assumed until the "
        "amending regulations are made. Only for occupied property of a firm "
        "with one property, and not for a charity, which gets charitable "
        "relief instead. Not modelled: relief kept on the main property when "
        "the other properties are each under £2,900 and in total under "
        "£20,000 (£28,000 in London), the grace period after taking on a "
        "second property, and the exclusion of vape shops."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA",
        "https://www.legislation.gov.uk/uksi/2023/1250/regulation/3",
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
        # Sch 4ZA para 4(1): chargeable amount = gross / E. In the taper,
        # E = band width / (rateable value - full threshold), "calculated to
        # three decimal places only" (SI 2023/1250 reg 3(4)).
        in_taper = (rateable_value > full_threshold) & (rateable_value <= taper_end)
        excess = where(in_taper, rateable_value - full_threshold, 1)
        e = np.round(
            (taper_end - full_threshold).astype(np.float64) / excess.astype(np.float64),
            3,
        )
        taper_relief = gross * (1 - 1 / e)
        relief = select(
            [rateable_value <= full_threshold, in_taper],
            [gross, taper_relief],
            default=0,
        )
        eligible = (firm("firm_n_properties", period) == 1) & ~firm(
            "firm_is_charity", period
        )
        in_england = firm("firm_rates_in_england", period)
        return where(eligible & in_england, relief, 0)
