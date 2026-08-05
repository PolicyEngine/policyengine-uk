from policyengine_uk.model_api import *


class uc_deductions(Variable):
    label = "UC deductions"
    documentation = (
        "Money deducted from this benefit unit's Universal Credit award to "
        "repay debts: advance repayments, government debt (benefit and tax "
        "credit overpayments) and third party deductions. Capped at the "
        "award itself."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        rate = benunit("uc_deduction_rate", period)
        standard_allowance = benunit("uc_standard_allowance", period)
        award = max_(
            benunit("universal_credit_pre_benefit_cap", period)
            - benunit("benefit_cap_reduction", period),
            0,
        )
        return min_(rate * standard_allowance, award)
