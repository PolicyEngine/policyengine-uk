from policyengine_uk.model_api import *


class council_tax_reduction_relevant_income_based_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = "CTR claimant has an income-based passporting benefit"
    documentation = (
        "Whether the Council Tax Reduction applicant or partner is on Income "
        "Support, income-based Jobseeker's Allowance or income-related "
        "Employment and Support Allowance. These are the benefit unit's "
        "awards, which belong to its claimant and partner, so they do not "
        "passport a household head who applies alone "
        "(council_tax_reduction_head_applies_alone)."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        income_based_benefit = (
            add(benunit, period, ["income_support", "jsa_income", "esa_income"]) > 0
        )
        head_applies_alone = benunit("council_tax_reduction_head_applies_alone", period)
        return income_based_benefit & ~head_applies_alone
