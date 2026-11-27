from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_business_rates(Variable):
    value_type = float
    entity = Firm
    label = "Business rates of the firm"
    documentation = (
        "Net business rates (non-domestic rates) the firm pays in England, "
        "Wales, Scotland or Northern Ireland: gross rates less reliefs, not "
        "below zero. The firm's rateable value (the net annual value in "
        "Northern Ireland) is treated as one aggregate property. Northern "
        "Ireland is modelled from 2023-24 where firm_northern_ireland_district "
        "is set, and gives 0 otherwise."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1988/41/schedule/4ZA"

    def formula(firm, period, parameters):
        gross = firm("firm_gross_business_rates", period)
        reliefs = firm("firm_business_rates_reliefs", period)
        return max_(gross - reliefs, 0)
