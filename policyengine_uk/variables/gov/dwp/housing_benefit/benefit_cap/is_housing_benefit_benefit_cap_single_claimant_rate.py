from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_unit import has_sixteen_year_old_dependant


class is_housing_benefit_benefit_cap_single_claimant_rate(Variable):
    value_type = bool
    entity = BenUnit
    label = "Housing Benefit benefit cap single claimant rate applies"
    documentation = (
        "Whether the Housing Benefit claimant is a single claimant (HB Regs "
        "2006 reg. 75CA(2)(a) and (c)): a claimant who neither has a partner "
        "nor is a lone parent, that is, responsible for a child or young "
        "person in the same household (reg. 2(1)). Housing Benefit has no "
        "claim by a member of a couple as a single person, so a couple has "
        "the other rate even where the partner could not be a joint claimant "
        "for Universal Credit. A 16-year-old member counts as a young person "
        "for the year (reg. 19(1); Child Benefit (General) Regulations 2006 "
        "regs. 5 and 7)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75CA",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/19",
    )

    def formula(benunit, period, parameters):
        return benunit("is_single_person", period) & ~has_sixteen_year_old_dependant(
            benunit, period
        )
