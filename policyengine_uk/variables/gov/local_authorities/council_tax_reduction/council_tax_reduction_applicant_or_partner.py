from policyengine_uk.model_api import *


class council_tax_reduction_applicant_or_partner(Variable):
    value_type = bool
    entity = Person
    label = "Applicant for Council Tax Reduction, or the applicant's partner"
    documentation = (
        "The people whose circumstances set a family's Council Tax Reduction "
        "scheme and its exemption from non-dependant deductions: the "
        "applicant and the applicant's partner. In a family that claims, the "
        "applicant is a member the model treats as liable for the council "
        "tax, and the partner is the other member of the couple where the "
        "applicant is the family's claimant or partner, whatever the "
        "partner's age. A household head who is not the claimant or partner "
        "of their family (a grandparent heading a family formed around a "
        "young couple, say) applies alone. In a family that cannot claim, "
        "these are the claimant and partner, who would apply if it could."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/3",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/3",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/3",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/12",
    )

    def formula(person, period, parameters):
        liable = person("council_tax_reduction_liable_person", period)
        claimant_or_partner = person("is_claimant_or_partner", period)
        family_claims = person.benunit.any(liable)
        # The couple, where one of them is liable; a partner under 18 is not
        # liable but is still the applicant's partner.
        couple_applies = person.benunit.any(liable & claimant_or_partner)
        applicant_or_partner = liable | (couple_applies & claimant_or_partner)
        return where(family_claims, applicant_or_partner, claimant_or_partner)
