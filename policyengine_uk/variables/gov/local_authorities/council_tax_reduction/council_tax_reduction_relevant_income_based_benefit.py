from policyengine_uk.model_api import *


class council_tax_reduction_relevant_income_based_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = "CTR claimant has an income-based passporting benefit"
    documentation = (
        "Whether the applicant or partner is on Income Support, income-based "
        "JSA or income-related ESA, which passports the working-age council "
        "tax reduction schemes to their maximum reduction. Only the "
        "applicant's and partner's awards count: another member of the "
        "benefit unit, such as a non-dependent adult, who has an award of "
        "their own claims in their own right."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2012/2886/schedule"

    def formula(benunit, period, parameters):
        return (
            add(
                benunit,
                period,
                [
                    "income_support",
                    "claimant_or_partner_jsa_income",
                    "claimant_or_partner_esa_income",
                ],
            )
            > 0
        )
