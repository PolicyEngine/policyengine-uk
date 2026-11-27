from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_uk_digital_services_revenues(Variable):
    value_type = float
    entity = Firm
    label = "Firm UK digital services revenues"
    documentation = "The firm's revenues from its digital services activity arising in connection with UK users in the accounting period (Finance Act 2020 ss.40-45). Defaults to 0."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2020/14/section/40"
