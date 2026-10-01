from policyengine_uk.model_api import *


class uc_deductions(Variable):
    label = "UC deductions"
    documentation = (
        "Money deducted from this benefit unit's Universal Credit award to "
        "repay debts: advance repayments, government debt (benefit and tax "
        "credit overpayments) and third party deductions. Deductions leave "
        "at least one penny per assessment period payable (Schedule 6 of "
        "SI 2013/380). Per-household statistics are validated against the "
        "DWP deductions statistics; weighted aggregates are not, because "
        "they scale with the model's UC caseload, which falls short of the "
        "administrative count. Annualized from the surveyed monthly rate: "
        "for deduction types with spells shorter than a year (e.g. advance "
        "recovery), annual per-household amounts are upper bounds."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.deductions
        rate = benunit("uc_deduction_rate", period)
        standard_allowance = benunit("uc_standard_allowance", period)
        award = max_(
            benunit("universal_credit_pre_benefit_cap", period)
            - benunit("benefit_cap_reduction", period),
            0,
        )
        minimum_payable = p.minimum_payable * MONTHS_IN_YEAR
        return min_(rate * standard_allowance, max_(award - minimum_payable, 0))
