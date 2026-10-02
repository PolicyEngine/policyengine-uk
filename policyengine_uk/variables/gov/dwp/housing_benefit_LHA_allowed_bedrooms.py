from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_allowed_bedrooms import (
    bedrooms_for_children,
)


def housing_benefit_occupiers(benunit, period):
    """Person masks for a family's Housing Benefit size criteria:
    ``occupier``, everyone who occupies the dwelling as their home rather
    than being placed with a family as a foster child or for adoption; and
    ``other_occupier``, the occupiers of other families who count in the
    household head's family's size criteria (a non-dependant's, boarder's or
    lodger's family, but not a sharer of the rent's)."""
    person = benunit.members
    # HB Regs 2006 reg 21(3): a child or young person placed with the
    # claimant or partner as a foster child or for adoption does not occupy
    # the claimant's dwelling. Reg 21(3) names only placements with the
    # claimant or partner; the model follows DWP in treating a child placed
    # with anyone in the household as no occupier (LHA Guidance Manual para
    # 2.033; HB circular A21/2013 para 22), as Universal Credit does (UC Sch 4
    # para 9(2)(g)).
    occupier = ~person("is_child_or_young_person_placed_with_family", period)
    head_family = person.benunit.any(person("is_household_head", period))
    sharer = person.benunit("liable_for_share_of_household_rent", period)
    # Reg 13D(3) for occupiers outside the family, as defined in 13D(12):
    # everyone in a non-dependant's, boarder's or lodger's family, including
    # their children.
    other_occupier = ~head_family & ~sharer & occupier
    return occupier, other_occupier


def housing_benefit_bedrooms_if_able_to_share(benunit, period):
    """Bedrooms in the Housing Benefit size criteria (HB Regs 2006 reg
    13D(3)-(3B)) as if every child and every member of a couple could share
    a bedroom. The reg 13D(3) proviso compares the dwelling's bedrooms with
    this entitlement."""
    person = benunit.members
    # A child is a person under 16 (HB Regs 2006 reg 2(1)).
    aged_16_or_over = person("age", period) >= 16
    occupier, other_occupier = housing_benefit_occupiers(benunit, period)
    # HB Regs 2006 reg 13D(3)(b): a person who is not a child, here a member
    # of the benefit unit other than the claimant or partner.
    family_rooms = benunit.sum(
        aged_16_or_over & ~person("is_claimant_or_partner", period) & occupier
    )
    # Reg 13D(3)(a): a couple, here the claimant and partner of an occupier's
    # family, has one bedroom; (b): every other occupier aged 16 or over has
    # their own. Each member of a couple counts as half, and only where both
    # members are counted, so the halves always pair.
    counted = other_occupier & aged_16_or_over
    claimant_or_partner = counted & person("is_claimant_or_partner", period)
    couple = (person.benunit.sum(claimant_or_partner) == 2) & person.benunit(
        "is_couple", period
    )
    occupier_rooms = counted * where(claimant_or_partner & couple, 0.5, 1)
    is_head_family = benunit.any(person("is_household_head", period))
    other_occupiers = is_head_family * benunit.max(person.household.sum(occupier_rooms))
    # Reg 13D(3)(c)-(e): the occupiers' children, the claimant's own and other
    # families', share rooms with each other.
    children = bedrooms_for_children(
        benunit,
        period,
        own_child=occupier,
        other_child=other_occupier,
    )
    # Reg 13D(3A) and (3B): additional bedrooms.
    additional = benunit("housing_benefit_LHA_additional_bedrooms", period)
    return 1 + family_rooms + other_occupiers + children + additional


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
        "partner, has one bedroom between them, or one each if a member "
        "cannot share a bedroom with the other because of disability. The "
        "children of a non-dependant, boarder or lodger are occupiers too, "
        "and share rooms with the claimant's children, except that a child "
        "who cannot share because of disability has a room of their own (see "
        "housing_benefit_LHA_cannot_share_bedrooms). A child or young person "
        "placed with a family in the household as a foster child or for "
        "adoption is not an occupier. A sharer's, boarder's or lodger's own "
        "claim counts only their own family."
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
        # Reg 13D(3)(za), (zb) and (ba): the further bedrooms for children and
        # members of couples who cannot share, where the dwelling has them.
        return housing_benefit_bedrooms_if_able_to_share(benunit, period) + benunit(
            "housing_benefit_LHA_cannot_share_bedrooms", period
        )
