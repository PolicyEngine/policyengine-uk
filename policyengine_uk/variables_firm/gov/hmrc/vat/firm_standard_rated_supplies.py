from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_standard_rated_supplies(Variable):
    value_type = float
    entity = Firm
    label = "Standard-rated supplies"
    definition_period = YEAR
    unit = GBP
    documentation = "Value of supplies subject to standard VAT rate (20%)"
