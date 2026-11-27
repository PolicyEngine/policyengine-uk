from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_non_banking_group_relief_claimed(Variable):
    value_type = float
    entity = Firm
    label = "Firm non-banking group relief claimed"
    documentation = "For a banking company, the part of its group relief claimed (Parts 5 and 5A) that was surrendered by non-banking companies. It is added back to the bank surcharge profits (CTA 2010 ss.269DA and 269DB). Defaults to 0."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/269DB"
