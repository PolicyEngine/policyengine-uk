from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_standard_rated_supplies(Variable):
    label = "Standard-rated supplies"
    documentation = (
        "Value of the firm's standard-rated supplies in the year, excluding VAT."
    )
    entity = Firm
    definition_period = YEAR
    hidden_input = True
    value_type = float
    unit = GBP
