from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_corporation_tax_upper_limit(Variable):
    value_type = float
    entity = Firm
    label = "Firm corporation tax upper limit"
    documentation = (
        "The upper limit divided by one plus the number of associated "
        "companies. Short accounting periods are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/18D"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax.marginal_relief
        associates = firm("firm_n_associated_companies", period)
        return p.upper_limit / (1 + associates)
