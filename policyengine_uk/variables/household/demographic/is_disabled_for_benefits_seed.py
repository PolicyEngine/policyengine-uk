from policyengine_uk.model_api import *


class is_disabled_for_benefits_seed(Variable):
    value_type = float
    entity = Person
    label = "Random seed for disability benefits eligibility determination"
    definition_period = YEAR
