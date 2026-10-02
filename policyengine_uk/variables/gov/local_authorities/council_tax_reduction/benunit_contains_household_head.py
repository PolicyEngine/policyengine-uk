from policyengine_uk.model_api import *


class benunit_contains_household_head(Variable):
    value_type = bool
    entity = BenUnit
    label = "Benefit unit contains the household head"
    documentation = (
        "Whether the household head is in this family. The head is the "
        "household reference person: a householder, in whose name the "
        "accommodation is owned or rented. Council Tax Reduction takes the "
        "head as the resident liable for the council tax under the Local "
        "Government Finance Act 1992 (s.6 in England and Wales, s.75 in "
        "Scotland), which every class of applicant requires. Each household "
        "has exactly one head. Where the input flags more than one member, "
        "the eldest flagged member is the head; where it flags none, the "
        "eldest member is. Rent and non-dependant rules for Universal Credit "
        "and Housing Benefit read is_household_head directly, so they agree "
        "with this only where exactly one member is flagged."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/14/section/6",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/75",
    )

    def formula(benunit, period, parameters):
        return benunit.any(
            benunit.members("council_tax_reduction_household_head", period)
        )
