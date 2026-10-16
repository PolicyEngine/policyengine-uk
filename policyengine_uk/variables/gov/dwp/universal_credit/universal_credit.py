from policyengine_uk.model_api import *


class universal_credit(Variable):
    label = "Universal Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "claims_universal_credit"

    def formula(benunit, period, parameters):
        uc_max_entitlement = benunit("universal_credit_pre_benefit_cap", period)
        # Both components already reflect the protected minimum floor (zero,
        # and so inactive, under current law), so the reported components sum
        # to the reduction actually applied. Summing them before subtracting
        # keeps main's float arithmetic, so current-law awards are unchanged
        # to the bit.
        benefit_cap_reduction = benunit("uc_benefit_cap_reduction", period)
        deductions = benunit("uc_deductions", period)
        return max_(uc_max_entitlement - (benefit_cap_reduction + deductions), 0)
