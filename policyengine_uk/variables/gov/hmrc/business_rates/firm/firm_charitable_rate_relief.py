from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_charitable_rate_relief(Variable):
    value_type = float
    entity = Firm
    label = "Mandatory charitable rate relief of the firm"
    documentation = (
        "80% of gross business rates for an occupied property of a charity in "
        "England. The private school exclusion and the zero rating of empty "
        "charity property are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA"
    defined_for = "firm_property_occupied"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.business_rates.reliefs.charity
        gross = firm("firm_gross_business_rates", period)
        is_charity = firm("firm_is_charity", period)
        in_england = firm("firm_rates_in_england", period)
        return where(is_charity & in_england, gross * p.rate, 0)
