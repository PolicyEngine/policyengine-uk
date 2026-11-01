from policyengine_uk.model_api import *


class in_receipt_of_guarantee_credit(Variable):
    label = "in receipt of Guarantee Credit"
    documentation = (
        "Whether the claimant or partner in this benefit unit is in receipt of "
        "a guarantee credit: the benefit unit is eligible for Pension Credit, "
        "claims it, is paid Pension Credit, and its Guarantee Credit is "
        "positive. A Guarantee Credit computed for a family that does not "
        "claim Pension Credit, or that the model does not treat as eligible "
        "for it (for example a working-age family), is not received, and "
        "nor is one under a reform that stops Pension Credit being paid. A "
        "mixed-age couple that keeps Pension Credit under the SI 2019/37 "
        "article 4 saving is eligible (meets_pension_credit_age_conditions), "
        "so it is in receipt when it claims, is paid Pension Credit and its "
        "Guarantee Credit is positive. Under the Pension Credit freeze the "
        "baseline receipt is kept while Pension Credit is still paid, because "
        "the frozen award is the baseline award."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/2",
        "https://www.legislation.gov.uk/ukpga/1992/5/section/1",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
    )

    def formula(benunit, period, parameters):
        paid = benunit("pension_credit", period) > 0
        freeze = parameters(period).gov.contrib.freeze_pension_credit
        baseline = benunit.simulation.baseline
        if freeze and baseline is not None:
            return paid & baseline.populations["benunit"](
                "in_receipt_of_guarantee_credit", period
            )
        eligible = benunit("is_pension_credit_eligible", period)
        would_claim = benunit("would_claim_pc", period)
        guarantee_credit = benunit("guarantee_credit", period)
        return eligible & would_claim & paid & (guarantee_credit > 0)
