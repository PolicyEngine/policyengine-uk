from policyengine_uk.model_api import *


class uc_deductions(Variable):
    label = "UC deductions"
    documentation = (
        "Money deducted from this benefit unit's Universal Credit award to "
        "repay debts: advance repayments, government debt (benefit and tax "
        "credit overpayments) and third party deductions. Deductions leave "
        "at least one penny per assessment period payable (Schedule 6, "
        "paragraph 3(1)(a) of SI 2013/380). Per-household statistics are "
        "validated against the DWP deductions statistics; weighted "
        "aggregates are not, because they scale with the model's UC "
        "caseload, which falls short of the administrative count."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "would_claim_uc"

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
        deductions = min_(rate * standard_allowance, max_(award - minimum_payable, 0))
        # The protected minimum floor (zero, and so inactive, under current
        # law) limits deductions and benefit cap reductions combined. The
        # benefit cap reduction absorbs it first, so deductions bend only
        # where they alone exceed the floor allowance: under the Fair
        # Repayment Rate the 15% deductions cap equals a typical 15% floor
        # allowance, so cappable deductions essentially never breach the
        # floor on their own. The floor does bind on the above-cap excess
        # that current law exempts from the deductions cap (last resort and
        # child maintenance deductions). JRF's briefing does not say whether
        # their floor exempts those categories - its worked example involves
        # only cappable deductions and the benefit cap - so this is a
        # modeling choice, tracked for follow-up.
        return min_(deductions, benunit("uc_maximum_reduction", period))
