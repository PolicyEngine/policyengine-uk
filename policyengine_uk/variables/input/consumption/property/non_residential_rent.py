from policyengine_uk.model_api import *


class non_residential_rent(Variable):
    label = "Non-residential rent"
    documentation = "The total amount of rent paid by the household in the year for non-residential property."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
