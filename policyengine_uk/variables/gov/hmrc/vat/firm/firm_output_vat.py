from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_output_vat(Variable):
    label = "Output VAT"
    documentation = (
        "VAT due on the firm's standard- and reduced-rated supplies. "
        "Zero-rated and exempt supplies carry no output VAT."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1994/23/section/2"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.vat
        standard = firm("firm_standard_rated_supplies", period)
        reduced = firm("firm_reduced_rated_supplies", period)
        return standard * p.standard_rate + reduced * p.reduced_rate
