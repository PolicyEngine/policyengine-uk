from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_group_digital_services_revenues(Variable):
    value_type = float
    entity = Firm
    label = "Firm group worldwide digital services revenues"
    documentation = "Worldwide digital services revenues of the group the firm belongs to, for the £500 million threshold (Finance Act 2020 s.46). Defaults to 0, read as the group's UK revenues."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2020/14/section/46"
