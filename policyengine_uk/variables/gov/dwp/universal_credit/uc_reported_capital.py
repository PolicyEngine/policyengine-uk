from policyengine_uk.model_api import *


class uc_reported_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "reported Universal Credit capital"
    documentation = (
        "Claimant-level capital for Universal Credit when household-level asset "
        "data cannot be attributed across multiple benefit units."
    )
    definition_period = YEAR
    unit = GBP
