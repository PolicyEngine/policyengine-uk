from policyengine_uk.model_api import *


class in_receipt_of_guarantee_credit(Variable):
    label = "in receipt of Guarantee Credit"
    documentation = (
        "Whether the claimant or partner in this benefit unit is in receipt of "
        "a guarantee credit: the Pension Credit paid to the benefit unit "
        "includes a Guarantee Credit. A Guarantee Credit computed for a family "
        "that does not claim Pension Credit, or is not eligible for it (for "
        "example a mixed-age couple), is not received. Under the Pension "
        "Credit freeze the baseline receipt is kept, because the frozen award "
        "is the baseline award."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/26",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/24",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
    )

    def formula(benunit, period, parameters):
        freeze = parameters(period).gov.contrib.freeze_pension_credit
        baseline = benunit.simulation.baseline
        if freeze and baseline is not None:
            return baseline.populations["benunit"](
                "in_receipt_of_guarantee_credit", period
            )
        pension_credit = benunit("pension_credit", period)
        guarantee_credit = benunit("guarantee_credit", period)
        return (pension_credit > 0) & (guarantee_credit > 0)
