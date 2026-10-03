from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_allowed_bedrooms import (
    bedrooms_for_children,
)
from policyengine_uk.variables.household.consumption.rent.non_dependant_normally_resides_with import (
    non_dependants_residing_with,
)


def housing_benefit_other_occupiers(benunit, period, other_occupier):
    """For each family, the sum of ``other_occupier`` (a count or weight for
    each occupier outside every family liable for the household's rent, zero
    for anyone else) over the people who occupy its dwelling (HB Regs 2006
    reg 13D(12)). A boarder or lodger, who
    pays the householder, counts for the household head's family. A
    non-dependant counts for each joint occupier they normally reside with
    (LHA Guidance Manual paras 2.093 and 2.110; see
    non_dependant_normally_resides_with)."""
    person = benunit.members
    boarder_or_lodger = person("pays_rent_to_householder", period)
    head_family = benunit.any(person("is_household_head", period))
    of_householder = head_family * benunit.max(
        person.household.sum(other_occupier * boarder_or_lodger)
    )
    non_dependants = non_dependants_residing_with(
        benunit, period, other_occupier * ~boarder_or_lodger
    )
    return of_householder + non_dependants


class housing_benefit_LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "Bedrooms in the Housing Benefit size criteria"
    documentation = (
        "Housing Benefit size criteria: one bedroom for the claimant or "
        "couple, one for each other occupier aged 16 or over, the bedrooms "
        "for the occupiers' children, and the additional bedrooms for "
        "overnight care and qualifying parents or carers (see "
        "housing_benefit_LHA_additional_bedrooms). Occupiers are everyone "
        "who lives in the dwelling as their home except a joint tenant "
        "outside the claimant's household. So every member of the benefit "
        "unit aged 16 or over who is not the claimant or partner adds a "
        "bedroom, such as a young person in full-time education; so do a "
        "householder's boarder or lodger and a non-dependant, but a sharer "
        "of the rent does not. A couple, such as a non-dependant and their "
        "partner, has one bedroom between them. The children of a "
        "non-dependant, boarder or "
        "lodger are occupiers too, and share rooms with the claimant's "
        "children. A child or young person placed with a family in the "
        "household as a foster child or for adoption is not an occupier. "
        "Where the rent is shared, a non-dependant and their children count "
        "for each joint occupier they normally reside with, by default every "
        "one (see non_dependant_normally_resides_with), while a boarder or "
        "lodger, who pays the household head, counts for the head's family "
        "only. A boarder's or lodger's own claim counts only their own "
        "family."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/21",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # A child is a person under 16 (HB Regs 2006 reg 2(1)).
        aged_16_or_over = person("age", period) >= 16
        # HB Regs 2006 reg 21(3): a child or young person placed with the
        # claimant or partner as a foster child or for adoption does not
        # occupy the claimant's dwelling. Reg 21(3) names only placements
        # with the claimant or partner; the model follows DWP in treating a
        # child placed with anyone in the household as no occupier (LHA
        # Guidance Manual para 2.033; HB circular A21/2013 para 22), as
        # Universal Credit does (UC Sch 4 para 9(2)(g)).
        occupier = ~person("is_child_or_young_person_placed_with_family", period)
        # HB Regs 2006 reg 13D(3)(b): a person who is not a child, here a
        # member of the benefit unit other than the claimant or partner.
        family_rooms = benunit.sum(
            aged_16_or_over & ~person("is_claimant_or_partner", period) & occupier
        )
        head_family = person.benunit.any(person("is_household_head", period))
        sharer = person.benunit("liable_for_share_of_household_rent", period)
        # Reg 13D(3) for occupiers outside the family, as defined in 13D(12):
        # everyone in a non-dependant's, boarder's or lodger's family,
        # including their children.
        other_occupier = ~head_family & ~sharer & occupier
        # Reg 13D(3)(a): a couple, here the claimant and partner of an
        # occupier's family, has one bedroom; (b): every other occupier aged
        # 16 or over has their own. Each member of a couple counts as half,
        # and only where both members are counted, so the halves always pair.
        counted = other_occupier & aged_16_or_over
        claimant_or_partner = counted & person("is_claimant_or_partner", period)
        couple = (person.benunit.sum(claimant_or_partner) == 2) & person.benunit(
            "is_couple", period
        )
        occupier_rooms = counted * where(claimant_or_partner & couple, 0.5, 1)
        other_occupiers = housing_benefit_other_occupiers(
            benunit, period, occupier_rooms
        )
        # Reg 13D(3)(c)-(e): the occupiers' children, the claimant's own and
        # other families', share rooms with each other.
        children = bedrooms_for_children(
            benunit,
            period,
            own_child=occupier,
            other_child=other_occupier,
            count_other=lambda mask: housing_benefit_other_occupiers(
                benunit, period, mask
            ),
        )
        # Reg 13D(3A) and (3B): additional bedrooms.
        additional = benunit("housing_benefit_LHA_additional_bedrooms", period)
        return 1 + family_rooms + other_occupiers + children + additional
