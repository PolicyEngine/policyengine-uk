from policyengine_uk.model_api import *


class in_receipt_of_savings_credit_only(Variable):
    label = "in receipt of Savings Credit only"
    documentation = (
        "Whether the claimant or partner in this benefit unit has an award of Pension "
        "Credit comprising only the savings credit: the benefit unit is eligible for "
        "Pension Credit, claims it, is paid Pension Credit, its Savings Credit is "
        "positive and it has no Guarantee Credit. A Savings Credit computed under a "
        "reform that stops Pension Credit being paid is not received; under "
        "disable_simulated_benefits, which sets Pension Credit to the reported amount, "
        "receipt also needs reported Pension Credit. A payment stands in for the "
        "award: the model does not withhold payment of awards of less than 10 pence a "
        "week (State Pension Credit Regulations 2002 reg 13), so every claimed award "
        "is paid; modelling that rule would need this to test the award, not the "
        "payment. Under the Pension Credit freeze the baseline receipt is kept while "
        "Pension Credit is still paid, because the frozen award is the baseline award."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/3",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/13",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
    )

    def formula(benunit, period, parameters):
        paid = benunit("pension_credit", period) > 0
        freeze = parameters(period).gov.contrib.freeze_pension_credit
        baseline = benunit.simulation.baseline
        if freeze and baseline is not None:
            return paid & baseline.populations["benunit"](
                "in_receipt_of_savings_credit_only", period
            )
        eligible = benunit("is_pension_credit_eligible", period)
        would_claim = benunit("would_claim_pc", period)
        guarantee_credit = benunit("guarantee_credit", period)
        savings_credit = benunit("savings_credit", period)
        return (
            eligible
            & would_claim
            & paid
            & (guarantee_credit <= 0)
            & (savings_credit > 0)
        )
