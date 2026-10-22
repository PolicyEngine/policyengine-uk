from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.deductions._reduction_allocation import (
    allocate_uc_reductions,
)


class uc_benefit_cap_reduction_after_floor(Variable):
    label = "UC benefit cap reduction applied"
    documentation = (
        "Benefit cap reduction actually taken off this benefit unit's "
        "Universal Credit award. Under current law this is "
        "uc_benefit_cap_reduction (the regulation 81 amount), bounded by the "
        "award: a cap reduction larger than the award takes the award to "
        "zero and no further. Where a protected minimum floor binds, "
        "deductions are met first, up to the floor allowance, and this takes "
        "whatever allowance is left. uc_benefit_cap_reduction itself stays "
        "gross, because benefit_cap_reduction and the deduction incidence "
        "read it, and the floor is a reform to the award, not to the cap."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "claims_universal_credit"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.deductions
        # JRF's September 2026 example (standard allowance £98 a week, a £15
        # Fair Repayment Rate deduction, an £80 cap reduction, an 85% floor)
        # limits the total to £15. Meeting the deduction first, as here,
        # removes the whole cap reduction.
        _, cap_reduction = allocate_uc_reductions(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("uc_benefit_cap_reduction", period),
            benunit("uc_deduction_demand", period),
            benunit("uc_maximum_reduction", period),
            p.minimum_payable * MONTHS_IN_YEAR,
        )
        return cap_reduction
