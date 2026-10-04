from policyengine_uk.model_api import *


class in_receipt_of_income_support_jsa_ib_or_esa_ir(Variable):
    label = "in receipt of Income Support, income-based JSA or income-related ESA"
    documentation = (
        "Whether this benefit unit is paid Income Support, income-based "
        "Jobseeker's Allowance or income-related Employment and Support "
        "Allowance: a positive amount of any of them. The model holds these "
        "awards at benefit-unit level, so it does not distinguish the claimant "
        "from the partner. The regulations also count as on income-based JSA "
        "or income-related ESA some days on which nothing is paid (a sanction, "
        "a waiting day, a loss-of-benefit restriction), which the model does "
        "not see."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/2",
    )

    def formula(benunit, period, parameters):
        return (
            (benunit("income_support", period) > 0)
            | (benunit("jsa_income", period) > 0)
            | (benunit("esa_income", period) > 0)
        )
