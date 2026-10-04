from policyengine_uk.model_api import *


class council_tax_reduction_claim_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "This family's Council Tax Reduction claim is a pensioner's"
    documentation = (
        "Whether this family's Council Tax Reduction claim falls under the "
        "pension-age rules. A person is a pensioner on their own and their "
        "partner's circumstances (SI 2012/2885 reg 3), so where families "
        "share the rent and each claims on its part, each claim follows the "
        "applicant's own family (council_tax_reduction_pensioner): a "
        "working-age sharer is not a pensioner because another family is, "
        "and a pensioner sharer stays one beside a mixed-age couple on "
        "Universal Credit. Where the household has a single claim, this is "
        "that claim's status (council_tax_reduction_household_has_pensioner)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/3",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/7",
    )

    def formula(benunit, period, parameters):
        household = benunit.household
        return where(
            household("council_tax_reduction_claims_are_joint", period),
            benunit("council_tax_reduction_pensioner", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
