from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_reduced_rated_supplies(Variable):
    value_type = float
    entity = Firm
    label = "Reduced-rated supplies"
    definition_period = YEAR
    unit = GBP
    documentation = "Value of supplies subject to reduced VAT rate (5%)"
