from policyengine_uk.model_api import *


class tv_licence_evasion_seed(Variable):
    value_type = float
    entity = Household
    label = "Random seed for TV licence evasion"
    definition_period = YEAR
