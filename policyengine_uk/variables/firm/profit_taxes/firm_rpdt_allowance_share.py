from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_rpdt_allowance_share(Variable):
    value_type = float
    entity = Firm
    label = "Firm share of the RPDT allowance"
    documentation = "Share of the residential property developer tax allowance allocated to the firm within its group (Finance Act 2022 s.43). Defaults to 1, a company with no other group member using the allowance. Values are clipped to between 0 and 1."
    definition_period = YEAR
    hidden_input = True
    unit = "/1"
    default_value = 1
    reference = "https://www.legislation.gov.uk/ukpga/2022/3/section/43"
