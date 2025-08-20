from policyengine_uk.model_api import *


class firm_standard_rated_supplies(Variable):
    value_type = float
    entity = Firm
    label = "Standard-rated supplies"
    definition_period = YEAR
    unit = GBP
    documentation = "Value of firm's supplies subject to standard VAT rate"
