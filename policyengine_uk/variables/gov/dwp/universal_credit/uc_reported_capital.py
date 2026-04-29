from policyengine_uk.model_api import *


class uc_reported_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "reported Universal Credit capital"
    documentation = (
        "Claimant-level capital for Universal Credit when household-level asset "
        "data cannot be attributed across multiple benefit units. Set to 0 to "
        "explicitly override the household proxy with zero assessable capital."
    )
    definition_period = YEAR
    unit = GBP
    default_value = -1
