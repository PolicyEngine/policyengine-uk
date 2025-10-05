from policyengine_uk.model_api import *


class would_claim_marriage_allowance(Variable):
    value_type = bool
    entity = Person
    label = "Would claim Marriage Allowance"
    documentation = (
        "Whether this person would claim Marriage Allowance if eligible. "
        "Generated stochastically in the dataset using take-up rates."
    )
    definition_period = YEAR
    default_value = True
