from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_gross_business_rates(Variable):
    value_type = float
    entity = Firm
    label = "Gross business rates of the firm before reliefs"
    documentation = (
        "Rateable value times the business rates multiplier, before any "
        "relief, for a firm's property in England. Zero outside England, "
        "whose rates are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA"

    def formula(firm, period, parameters):
        rateable_value = firm("firm_rateable_value", period)
        multiplier = firm("firm_business_rates_multiplier", period)
        in_england = firm("firm_in_england", period)
        return where(in_england, rateable_value * multiplier, 0)
