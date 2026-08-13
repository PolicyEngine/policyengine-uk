from policyengine_uk.model_api import *


class uc_benefit_cap_reduction(Variable):
    label = "UC benefit cap reduction"
    documentation = (
        "Benefit cap reduction actually taken off this benefit unit's "
        "Universal Credit award. Equal to benefit_cap_reduction under "
        "current law. Where a protected minimum floor is in force, the cap "
        "reduction absorbs the floor first, so only the part of it fitting "
        "in the allowance uc_deductions leaves is applied. "
        "benefit_cap_reduction itself stays gross, because it also applies "
        "to Housing Benefit, which the Universal Credit floor does not "
        "protect."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "would_claim_uc"

    def formula(benunit, period, parameters):
        reduction = benunit("benefit_cap_reduction", period)
        # Deductions take their share of the floor allowance first, so the
        # cap reduction is what bends when the floor binds. Under the Fair
        # Repayment Rate the 15% deductions cap equals a typical 15% floor
        # allowance, so cappable deductions alone essentially never breach
        # the floor - only benefit cap reductions push past it. JRF's worked
        # example (standard allowance £92, deduction £14, benefit cap £59,
        # floor £78) preserves the £14 deduction and eliminates the £59 cap
        # reduction, which is this ordering.
        headroom = max_(
            benunit("uc_maximum_reduction", period) - benunit("uc_deductions", period),
            0,
        )
        return min_(reduction, headroom)
