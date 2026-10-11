from policyengine_uk.model_api import *


class in_receipt_of_savings_credit_only(Variable):
    label = "in receipt of Savings Credit only"
    documentation = (
        "Whether the claimant or partner in this benefit unit has an award of "
        "Pension Credit comprising only the savings credit: the benefit unit is "
        "eligible for Pension Credit, claims it, its Savings Credit is positive "
        "and it has no Guarantee Credit. Under the Pension Credit freeze the "
        "baseline receipt is kept, because the frozen award is the baseline "
        "award."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/3",
    )

    def formula(benunit, period, parameters):
        freeze = parameters(period).gov.contrib.freeze_pension_credit
        baseline = benunit.simulation.baseline
        if freeze and baseline is not None:
            return baseline.populations["benunit"](
                "in_receipt_of_savings_credit_only", period
            )
        eligible = benunit("is_pension_credit_eligible", period)
        would_claim = benunit("would_claim_pc", period)
        guarantee_credit = benunit("guarantee_credit", period)
        savings_credit = benunit("savings_credit", period)
        return eligible & would_claim & (guarantee_credit <= 0) & (savings_credit > 0)
