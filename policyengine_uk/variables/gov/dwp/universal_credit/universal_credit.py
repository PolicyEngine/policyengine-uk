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
        benefit_cap_reduction = benunit("benefit_cap_reduction", period)
        deductions = benunit("uc_deductions", period)
        # A protected minimum floor (zero under current law) caps combined
        # benefit cap reductions and deductions at (1 - floor) x the standard
        # allowance, per JRF's protected minimum floor design (their worked
        # example limits the reduction itself to 15% of the standard
        # allowance). Zero means reductions are unlimited.
        floor_rate = parameters(
            period
        ).gov.dwp.universal_credit.deductions.protected_floor
        total_reductions = benefit_cap_reduction + deductions
        max_reductions = where(
            floor_rate > 0,
            (1 - floor_rate) * benunit("uc_standard_allowance", period),
            np.inf,
        )
        return max_(uc_max_entitlement - min_(total_reductions, max_reductions), 0)
