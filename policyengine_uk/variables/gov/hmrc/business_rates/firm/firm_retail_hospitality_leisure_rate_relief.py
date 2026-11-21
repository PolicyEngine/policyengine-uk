from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_retail_hospitality_leisure_rate_relief(Variable):
    value_type = float
    entity = Firm
    label = "Retail, hospitality and leisure business rates relief of the firm"
    documentation = (
        "Retail, hospitality and leisure (RHL) relief in England: 75% in "
        "2023-24 and 2024-25 and 40% in 2025-26 of the bill left after "
        "mandatory reliefs, capped at £110,000 per business. It ended on 31 "
        "March 2026. Only for occupied property. The subsidy control limits "
        "and the right to opt out are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.gov.uk/guidance/business-rates-relief-202526-retail-hospitality-and-leisure-scheme"
    defined_for = "firm_property_occupied"

    def formula(firm, period, parameters):
        p = parameters(
            period
        ).gov.hmrc.business_rates.reliefs.retail_hospitality_leisure
        gross = firm("firm_gross_business_rates", period)
        mandatory_reliefs = add(
            firm,
            period,
            ["firm_charitable_rate_relief", "firm_small_business_rate_relief"],
        )
        remaining = max_(gross - mandatory_reliefs, 0)
        is_rhl = firm("firm_is_rhl_property", period)
        return where(is_rhl, min_(remaining * p.rate, p.cap), 0)
