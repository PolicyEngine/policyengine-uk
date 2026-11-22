from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_exempt_supplies(Variable):
    label = "Exempt supplies"
    documentation = "Value of the firm's VAT-exempt supplies in the year."
    entity = Firm
    definition_period = YEAR
    hidden_input = True
    value_type = float
    unit = GBP
