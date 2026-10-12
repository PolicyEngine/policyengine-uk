from policyengine_uk.model_api import *


class would_claim_uc_childcare(Variable):
    value_type = bool
    entity = BenUnit
    label = "would claim the Universal Credit childcare element"
    documentation = (
        "Whether this family would claim the Universal Credit childcare element "
        "if entitled. Generated stochastically in a dataset from take-up rates "
        "so that the element's caseload matches the published one; for the "
        "policy calculator it defaults to True."
    )
    definition_period = YEAR
    default_value = True
