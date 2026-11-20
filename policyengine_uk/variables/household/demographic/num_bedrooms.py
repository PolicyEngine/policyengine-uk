from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class num_bedrooms(Variable):
    value_type = int
    entity = Household
    label = "The number of bedrooms in the house"
    documentation = (
        "The number of bedrooms in the dwelling (Family Resources Survey "
        "BEDROOM6, which is at least 1 and top-coded at 6). 0, the default, "
        "means not reported."
    )
    definition_period = YEAR
