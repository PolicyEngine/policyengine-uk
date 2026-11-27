from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_rpd_profits(Variable):
    value_type = float
    entity = Firm
    label = "Firm residential property developer tax profits"
    documentation = "The firm's RPD profits for the year, the profits of its residential property development activities as Finance Act 2022 Part 2 defines them, before the allowance. Defaults to 0."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2022/3/section/33"
