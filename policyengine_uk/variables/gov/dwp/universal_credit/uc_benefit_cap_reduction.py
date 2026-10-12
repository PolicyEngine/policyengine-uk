from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.deductions._reduction_allocation import (
    allocate_uc_reductions,
)


class uc_benefit_cap_reduction(Variable):
    label = "UC benefit cap reduction applied"
    documentation = (
        "Benefit cap reduction actually taken off this benefit unit's "
        "Universal Credit award. Under current law this is "
        "benefit_cap_reduction, bounded by the award: a cap reduction larger "
        "than the award takes the award to zero and no further. Where a "
        "protected minimum floor binds, deductions are met first, up to the "
        "floor allowance, and this takes whatever allowance is left. "
        "benefit_cap_reduction itself stays gross, because Housing Benefit "
        "also reads it and the Universal Credit floor does not protect "
        "Housing Benefit."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "would_claim_uc"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.deductions
        # JRF's September 2026 example (standard allowance £98 a week, a £15
        # Fair Repayment Rate deduction, an £80 cap reduction, an 85% floor)
        # limits the total to £15. Meeting the deduction first, as here,
        # removes the whole cap reduction.
        _, cap_reduction = allocate_uc_reductions(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("benefit_cap_reduction", period),
            benunit("uc_deduction_rate", period)
            * benunit("uc_standard_allowance", period),
            benunit("uc_maximum_reduction", period),
            p.minimum_payable * MONTHS_IN_YEAR,
        )
        return cap_reduction
