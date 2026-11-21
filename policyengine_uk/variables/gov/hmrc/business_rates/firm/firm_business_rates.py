from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_business_rates(Variable):
    value_type = float
    entity = Firm
    label = "Business rates of the firm"
    documentation = (
        "Net business rates the firm pays in England: gross rates less "
        "reliefs, not below zero. The firm's rateable value is treated as one "
        "aggregate property. Scotland, Wales and Northern Ireland are not "
        "modelled and give 0 (firm_in_england)."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA"

    def formula(firm, period, parameters):
        gross = firm("firm_gross_business_rates", period)
        reliefs = firm("firm_business_rates_reliefs", period)
        return max_(gross - reliefs, 0)
