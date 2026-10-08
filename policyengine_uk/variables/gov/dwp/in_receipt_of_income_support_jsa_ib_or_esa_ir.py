from policyengine_uk.model_api import *


class in_receipt_of_income_support_jsa_ib_or_esa_ir(Variable):
    label = "in receipt of Income Support, income-based JSA or income-related ESA"
    documentation = (
        "Whether this benefit unit is paid Income Support, income-based "
        "Jobseeker's Allowance or income-related Employment and Support "
        "Allowance: a positive amount of any of them on the claimant's or "
        "partner's award. A couple's award covers both of them, so the model "
        "does not distinguish the claimant from the partner. Another member of "
        "the benefit unit, who is neither the claimant, the partner nor a child "
        "or young person they are responsible for, claims in their own right, "
        "so their award does not count. The regulations also count as on "
        "income-based JSA or income-related ESA some days on which nothing is "
        "paid (a sanction, a waiting day, a loss-of-benefit restriction), which "
        "the model does not see."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/2",
    )

    def formula(benunit, period, parameters):
        # Income Support already needs the claimant's or partner's own award
        # (income_support_eligible).
        return (
            (benunit("income_support", period) > 0)
            | (benunit("claimant_or_partner_jsa_income", period) > 0)
            | (benunit("claimant_or_partner_esa_income", period) > 0)
        )
