from policyengine_uk.model_api import *


class council_tax_reduction_claims_are_joint(Variable):
    value_type = bool
    entity = Household
    label = "Families in the household claim Council Tax Reduction on their shares"
    documentation = (
        "Whether the household's rent is shared between families, so that "
        "each family liable for it is jointly liable for the council tax and "
        "claims Council Tax Reduction on its own part. Each such claim is "
        "then assessed on the applicant's own family: its scheme "
        "(council_tax_reduction_claim_pensioner) and its exemption from "
        "non-dependant deductions "
        "(council_tax_reduction_applicant_has_non_dep_exemption)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/14/section/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/7",
    )

    def formula(household, period, parameters):
        person = household.members
        return household.any(
            person.benunit("liable_for_share_of_household_rent", period)
        )
