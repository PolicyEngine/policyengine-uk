from policyengine_uk.model_api import *


class council_tax_reduction_household_has_pensioner(Variable):
    value_type = bool
    entity = Household
    label = "CTR household head's family has a pension-age applicant or partner"
    documentation = (
        "Whether the Council Tax Reduction applicant or partner "
        "(is_council_tax_reduction_applicant_or_partner) in the household "
        "head's family is over State Pension age, which stands in for the "
        "qualifying age for State Pension Credit."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/3",
    )

    def formula(household, period, parameters):
        person = household.members
        claimant_benunit = person.benunit("benunit_contains_household_head", period)
        applicant_or_partner = person(
            "is_council_tax_reduction_applicant_or_partner", period
        )
        return household.any(
            claimant_benunit & applicant_or_partner & person("is_SP_age", period)
        )
