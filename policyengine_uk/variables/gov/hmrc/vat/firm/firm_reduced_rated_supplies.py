from policyengine_uk.model_api import *


class firm_reduced_rated_supplies(Variable):
    value_type = float
    entity = Firm
    label = "Reduced-rated supplies"
    definition_period = YEAR
    unit = GBP
    documentation = "Value of firm's supplies subject to reduced VAT rate"
