from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.locations import BRMAName


class brma(Variable):
    value_type = Enum
    possible_values = BRMAName
    default_value = BRMAName.MAIDSTONE
    entity = Household
    label = "Broad Rental Market Area"
    definition_period = YEAR
