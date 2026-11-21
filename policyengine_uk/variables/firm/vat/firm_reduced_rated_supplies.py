from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_reduced_rated_supplies(Variable):
    label = "Reduced-rated supplies"
    documentation = (
        "Value of the firm's reduced-rated supplies in the year, excluding VAT."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
