from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_zero_rated_supplies(Variable):
    label = "Zero-rated supplies"
    documentation = "Value of the firm's zero-rated supplies in the year."
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
