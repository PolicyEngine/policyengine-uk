from policyengine_uk.model_api import *


class universal_credit(Variable):
    label = "Universal Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "would_claim_uc"

    def formula(benunit, period, parameters):
        uc_max_entitlement = benunit("universal_credit_pre_benefit_cap", period)
        # Both components are already limited by the protected minimum floor
        # (zero, and so inactive, under current law): uc_deductions takes its
        # share of the floor allowance first and uc_benefit_cap_reduction
        # takes what is left. Subtracting them separately, rather than
        # limiting their sum here, keeps the reported components summing to
        # the reduction actually applied.
        benefit_cap_reduction = benunit("uc_benefit_cap_reduction", period)
        deductions = benunit("uc_deductions", period)
        return max_(uc_max_entitlement - benefit_cap_reduction - deductions, 0)
