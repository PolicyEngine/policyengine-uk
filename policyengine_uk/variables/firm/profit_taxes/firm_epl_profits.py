from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_epl_profits(Variable):
    value_type = float
    entity = Firm
    label = "Firm energy profits levy profits"
    documentation = "The firm's profits chargeable to the energy profits levy: its ring fence profits adjusted as the Energy (Oil and Gas) Profits Levy Act 2022 requires, after the investment and decarbonisation allowances and levy loss relief. Defaults to 0."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2022/40/section/1"
