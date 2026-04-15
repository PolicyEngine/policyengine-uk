from policyengine_uk.model_api import *


class would_claim_parents_learning_allowance(Variable):
    value_type = bool
    entity = Person
    label = "Would claim Parents' Learning Allowance"
    documentation = (
        "Whether this person would claim Parents' Learning Allowance if eligible."
    )
    definition_period = YEAR
    default_value = True
