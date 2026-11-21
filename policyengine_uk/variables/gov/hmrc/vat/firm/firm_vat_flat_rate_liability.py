from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_vat_flat_rate_liability(Variable):
    label = "VAT liability under the flat rate scheme"
    documentation = (
        "Flat rate percentage times VAT-inclusive flat rate turnover. Input "
        "VAT is not recovered; recovery on capital goods over £2,000 is not "
        "modelled."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/1995/2518/regulation/55K"

    def formula(firm, period, parameters):
        rate = firm("firm_flat_rate_percentage", period)
        turnover = firm("firm_flat_rate_turnover", period)
        return rate * turnover
