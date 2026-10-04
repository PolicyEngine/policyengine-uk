from policyengine_uk.model_api import *


class council_tax_reduction_liable_person(Variable):
    value_type = bool
    entity = Person
    label = "Treated as liable for the council tax in Council Tax Reduction"
    documentation = (
        "Whether the model treats this person as liable to pay the household's "
        "council tax. Liability goes to the resident with the greatest "
        "interest in the dwelling, jointly where several hold the same "
        "interest, and to that person's resident spouse, civil partner or "
        "cohabiting partner. A resident is aged 18 or over. The model takes "
        "these as liable, each only if aged 18 or over: "
        "the household head; "
        "the head's partner, where the head is a claimant or partner of their "
        "family; "
        "and the claimant and partner of any family liable for a share of "
        "the household's rent. "
        "Other adults in the head's family, such as grown-up children or a "
        "young couple living in a grandparent's family, are not liable."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/14/section/6",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/9",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/75",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/77",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/77A",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/99",
    )

    def formula(person, period, parameters):
        adult = person("age", period) >= 18  # s.6(5), s.99(1)
        head = person("council_tax_reduction_household_head", period)
        claimant_or_partner = person("is_claimant_or_partner", period)
        head_is_claimant_or_partner = person.benunit.any(head & claimant_or_partner)
        head_family = person.benunit.any(head)
        heads_partner = head_family & head_is_claimant_or_partner & claimant_or_partner
        sharer = person.benunit("liable_for_share_of_household_rent", period)
        return adult & (head | heads_partner | (sharer & claimant_or_partner))
