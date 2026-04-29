from policyengine_uk.model_api import *


class income_support(Variable):
    value_type = float
    entity = BenUnit
    label = "Income Support"
    definition_period = YEAR
    unit = GBP
    defined_for = "would_claim_IS"

    def formula(benunit, period, parameters):
        if not parameters(period).gov.dwp.income_support.active:
            return benunit.empty_array()
        return benunit("income_support_entitlement", period)
