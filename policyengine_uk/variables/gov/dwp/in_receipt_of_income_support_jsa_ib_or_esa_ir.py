from policyengine_uk.model_api import *


class in_receipt_of_income_support_jsa_ib_or_esa_ir(Variable):
    label = "in receipt of Income Support, income-based JSA or income-related ESA"
    documentation = (
        "Whether this benefit unit is paid Income Support, income-based "
        "Jobseeker's Allowance or income-related Employment and Support "
        "Allowance: a positive amount of any of them on the claimant's or "
        "partner's award. A couple's award covers both of them, so the model "
        "does not distinguish the claimant from the partner. Anyone else in "
        "the benefit unit claims in their own right, so their award does not "
        "count: a non-dependent adult, or a young person with an award of "
        "their own, which is payable to them, not to the claimant. Income "
        "Support is already only the claimant's or partner's award. JSA and "
        "ESA are read through claimant_or_partner_jsa_income and "
        "claimant_or_partner_esa_income, so a jsa_income or esa_income "
        "entered for the benefit unit is taken to be the claimant's or "
        "partner's unless it equals the award the members' reports give, or "
        "their plain total, in which case it is read through the reports. "
        "The regulations also count as on "
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
