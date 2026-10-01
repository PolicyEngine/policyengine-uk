from policyengine_uk.model_api import *


class is_child_or_young_person_placed_with_family(Variable):
    value_type = bool
    entity = Person
    label = "Child or young person placed with the family by a local authority or for adoption"
    documentation = (
        "A child or young person (the Child Benefit definition) who is not "
        "the claimant or partner and is placed with their benefit unit by a "
        "local authority, such as a foster child (see "
        "is_looked_after_by_local_authority), or placed for adoption (see "
        "is_placed_for_adoption). Under Income Support, income-based "
        "Jobseeker's Allowance, income-related Employment and Support "
        "Allowance and Housing Benefit they are not a member of the "
        "claimant's household, and under Housing Benefit they do not occupy "
        "the claimant's dwelling. HB reg 21(3)(a) refers to a placement "
        "under section 22C(2) of the Children Act 1989; the model follows "
        "DWP's guidance that foster children are within reg 21(3) (LHA "
        "Guidance Manual para 2.033)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/21",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/16",
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/78",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/156",
        "https://assets.publishing.service.gov.uk/media/5a758238ed915d6faf2b38a2/lha-guidance-manual.pdf",
    )

    def formula(person, period, parameters):
        # HB Regs 2006 reg 21(3)(a)-(c); IS Regs 1987 reg 16(4); JSA Regs
        # 1996 reg 78(4); ESA Regs 2008 reg 156(5).
        placed = person("is_looked_after_by_local_authority", period) | person(
            "is_placed_for_adoption", period
        )
        return (
            placed
            & person("is_child_or_qualifying_young_person_for_child_benefit", period)
            & ~person("is_claimant_or_partner", period)
        )
