from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_zero_rated_supplies(Variable):
    value_type = float
    entity = Firm
    label = "Zero-rated supplies"
    definition_period = YEAR
    unit = GBP
    documentation = "Value of supplies subject to zero VAT rate (0%)"
