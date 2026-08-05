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
        # A protected minimum floor (zero under current law) limits how far
        # benefit cap reductions and deductions combined can reduce the award:
        # never below floor x standard allowance, where the pre-reduction
        # award reaches it.
        floor_rate = parameters(
            period
        ).gov.dwp.universal_credit.deductions.protected_floor
        floor = floor_rate * benunit("uc_standard_allowance", period)
        total_reductions = benefit_cap_reduction + deductions
        max_reductions = max_(uc_max_entitlement - floor, 0)
        return uc_max_entitlement - min_(total_reductions, max_reductions)
