from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class firm_region(Variable):
    value_type = Enum
    entity = Firm
    label = "Firm region"
    documentation = "ITL1 region (or nation) where the firm is based."
    definition_period = YEAR
    hidden_input = True
    possible_values = Region
    default_value = Region.LONDON
