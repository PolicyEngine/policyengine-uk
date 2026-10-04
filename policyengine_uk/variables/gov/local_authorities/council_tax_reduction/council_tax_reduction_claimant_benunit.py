from policyengine_uk.model_api import *


class council_tax_reduction_claimant_benunit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Family claims Council Tax Reduction for the household"
    documentation = (
        "Whether this family can claim Council Tax Reduction on the "
        "household's council tax. Where the household's rent is shared, every "
        "family liable for it is jointly and severally liable for the council "
        "tax and claims on its part, through a liable member who is not an "
        "excluded full-time student. Otherwise the family of the household's "
        "oldest adult claims, as before."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/14/section/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/75",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        rent_is_shared = benunit.household(
            "council_tax_reduction_claims_are_joint", period
        )
        # A full-time student is excluded from entitlement (Default Scheme
        # Sch para 75(1)); the model takes a person in higher education as
        # one, so a sharer family claims through a liable non-student.
        liable_family = benunit.any(
            person("is_liable_for_household_rent", period) & ~person("in_HE", period)
        )
        return where(
            rent_is_shared,
            liable_family,
            benunit("benunit_contains_household_head", period),
        )
