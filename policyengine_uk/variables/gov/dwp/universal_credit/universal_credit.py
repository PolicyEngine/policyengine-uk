from policyengine_uk.model_api import *


class universal_credit(Variable):
    label = "Universal Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "would_claim_uc"

    def formula(benunit, period, parameters):
        uc_max_entitlement = benunit(
            "universal_credit_pre_benefit_cap", period
        )
        benefit_cap_reduction = benunit("benefit_cap_reduction", period)
        return max_(uc_max_entitlement - benefit_cap_reduction, 0)
