from policyengine_uk.model_api import *


class uc_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit assessable capital"
    documentation = (
        "PolicyEngine UK's current proxy for Universal Credit assessable capital, "
        "using household liquid savings."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        return max_(0, benunit.household("savings", period))
