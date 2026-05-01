from policyengine_uk.model_api import *


class hounslow_council_tax_reduction_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Hounslow CTS assessable capital"
    documentation = (
        "Hounslow tests claimant and partner capital for working-age Council "
        "Tax Support. PolicyEngine UK does not currently store those stocks "
        "separately by claimant, partner, and non-dependant, so this uses "
        "household liquid savings as the available CTS capital proxy."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        return benunit.household("savings", period)
