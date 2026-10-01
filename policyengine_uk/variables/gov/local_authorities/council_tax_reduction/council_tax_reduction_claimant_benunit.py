from policyengine_uk.model_api import *


class council_tax_reduction_claimant_benunit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Family claims Council Tax Reduction for the household"
    documentation = (
        "Whether this family can claim Council Tax Reduction on the "
        "household's council tax. Where the household's rent is shared, every "
        "family liable for it is jointly and severally liable for the council "
        "tax and claims on its part. Otherwise the family of the household's "
        "oldest adult claims, as before."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/14/section/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/7",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        rent_is_shared = benunit.any(
            person.household.any(
                person.benunit("liable_for_share_of_household_rent", period)
            )
        )
        liable_family = benunit.any(person("is_liable_for_household_rent", period))
        return where(
            rent_is_shared,
            liable_family,
            benunit("benunit_contains_household_head", period),
        )
