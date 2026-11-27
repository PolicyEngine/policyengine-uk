from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_group_uk_digital_services_revenues(Variable):
    value_type = float
    entity = Firm
    label = "Firm group UK digital services revenues"
    documentation = "UK digital services revenues of the whole group the firm belongs to, for the threshold test and the allowance (Finance Act 2020 ss.46-47). Defaults to 0, read as the firm's own UK revenues."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2020/14/section/46"
