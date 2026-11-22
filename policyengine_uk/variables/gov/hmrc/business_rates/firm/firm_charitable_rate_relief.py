from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_charitable_rate_relief(Variable):
    value_type = float
    entity = Firm
    label = "Mandatory charitable rate relief of the firm"
    documentation = (
        "80% of gross business rates for an occupied property of a charity in "
        "England, Wales or Scotland: the ratepayer pays one fifth of the bill "
        "(LGFA 1988 Schedule 4ZA para 2 in England and Wales, s.43(5)-(6) "
        "before April 2024; Local Government (Financial Provisions etc.) "
        "(Scotland) Act 1962 s.4(2) in Scotland). How it combines with the "
        "Welsh and Scottish small business reliefs is set in "
        "firm_business_rates_reliefs. Not modelled: the private and "
        "independent school exclusions (England from April 2025, Wales from "
        "April 2025, Scotland from April 2022) and the zero rating of empty "
        "charity property."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA",
        "https://www.legislation.gov.uk/ukpga/1988/41/section/43/2023-04-01",
        "https://www.legislation.gov.uk/ukpga/1962/9/section/4",
    ]
    defined_for = "firm_property_occupied"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.business_rates.reliefs.charity
        gross = firm("firm_gross_business_rates", period)
        is_charity = firm("firm_is_charity", period)
        region = firm("firm_region", period)
        regions = region.possible_values
        in_england = firm("firm_rates_in_england", period)
        modelled = in_england | (region == regions.WALES) | (region == regions.SCOTLAND)
        return where(is_charity & modelled, gross * p.rate, 0)
