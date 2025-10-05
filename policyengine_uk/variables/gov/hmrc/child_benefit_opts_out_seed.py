from policyengine_uk.model_api import *


class child_benefit_opts_out_seed(Variable):
    value_type = float
    entity = BenUnit
    label = "Random seed for child benefit opt-out decision"
    definition_period = YEAR
