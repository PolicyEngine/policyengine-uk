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
        uc_entitlement = uc_max_entitlement - benefit_cap_reduction
        return max_(0, uc_entitlement)
