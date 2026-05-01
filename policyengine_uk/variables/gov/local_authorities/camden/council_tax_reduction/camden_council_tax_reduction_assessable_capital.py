from policyengine_uk.model_api import *


class camden_council_tax_reduction_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Camden CTR assessable capital"
    documentation = (
        "Camden tests claimant and partner savings or assets. PolicyEngine UK "
        "does not currently store those stocks separately by claimant, partner, "
        "and non-dependant, so this uses household liquid savings as the "
        "available CTR capital proxy."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        return benunit.household("savings", period)
