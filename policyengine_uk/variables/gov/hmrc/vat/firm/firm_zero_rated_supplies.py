from policyengine_uk.model_api import *


class firm_zero_rated_supplies(Variable):
    value_type = float
    entity = Firm
    label = "Zero-rated supplies"
    definition_period = YEAR
    unit = GBP
    documentation = "Value of firm's supplies subject to zero VAT rate"
