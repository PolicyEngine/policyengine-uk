from policyengine_uk.model_api import *


def child_bedrooms(boys_under_10, boys_10_to_15, girls_under_10, girls_10_to_15):
    """The fewest bedrooms that hold children two to a room, where two
    children may share if they are of the same sex or both under 10.

    The arguments count children under 16: boys and girls under 10, and boys
    and girls aged 10 to 15.
    """
    # First, have over-10s share where possible
    over_10_rooms = (boys_10_to_15 + 1) // 2 + (girls_10_to_15 + 1) // 2
    # There may children over 10 still not sharing
    space_for_boy_under_10 = boys_10_to_15 % 2
    space_for_girl_under_10 = girls_10_to_15 % 2
    # Have those spaces filled where possible by children under 10
    left_over_boys_under_10 = max_(boys_under_10 - space_for_boy_under_10, 0)
    left_over_girls_under_10 = max_(girls_under_10 - space_for_girl_under_10, 0)
    # The remaining children must share in pairs
    under_10_rooms = (left_over_boys_under_10 + left_over_girls_under_10 + 1) // 2
    return over_10_rooms + under_10_rooms


def bedrooms_for_children(
    benunit, period, own_child=None, other_child=None, counts_other_children=None
):
    """Bedrooms for the children under 16 in the family's size criteria.

    ``own_child`` marks the family's members counted as its children (by
    default, every member under 16). ``other_child`` marks people under 16 in
    other families of the household who count in this family's size
    criteria, such as a non-dependant's child; they share rooms with the
    family's own children. ``counts_other_children`` marks the families that
    count them (by default, every family). The children are allotted to the
    fewest bedrooms with child_bedrooms.
    """
    person = benunit.members
    age = person("age", period)
    male = person("is_male", period)
    under_16 = age < 16
    under_10 = age < 10
    if own_child is None:
        own_child = under_16
    own_child = own_child & under_16

    def count(group):
        own = benunit.sum(own_child & group)
        if other_child is None:
            return own
        others = benunit.max(person.household.sum(other_child & under_16 & group))
        if counts_other_children is None:
            return own + others
        return own + where(counts_other_children, others, 0)

    return child_bedrooms(
        count(under_10 & male),
        count(~under_10 & under_16 & male),
        count(under_10 & ~male),
        count(~under_10 & under_16 & ~male),
    )


class LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "The number of bedrooms covered by LHA for the benefit unit"
    documentation = (
        "Universal Credit size criteria for the renter's extended benefit "
        "unit: one bedroom for the renter or couple, one for each qualifying "
        "young person the renter is responsible for, one for each other "
        "member of the benefit unit aged 16 or over who is not the claimant, "
        "partner, household head or a foster child, one for each "
        "non-dependant aged 16 or over from another family, the children's "
        "bedrooms, and the additional bedrooms for overnight care and foster "
        "parents (see LHA_additional_bedrooms). The formula treats the "
        "household head as liable for the rent, so a head who does not claim "
        "is not a non-dependant (para 9(2)(d)); a head who is a qualifying "
        "young person the renter is responsible for keeps their bedroom. The "
        "children are the renter's own children and the children of the "
        "household's non-dependants, such as a grandchild whose parent lives "
        "with the renter; they share rooms with each other. A child or "
        "qualifying young person no one is responsible for, such as a foster "
        "child or another child looked after by a local authority, is not a "
        "non-dependant and has no bedroom, in this family or another; a "
        "child placed for adoption is the adopter's responsibility (reg "
        "4A(1)(c)) and counts. Joint tenants and other sharers of the rent, "
        "boarders and lodgers are not non-dependants, so neither they nor "
        "their children add a bedroom to anyone's entitlement; the "
        "household's non-dependants and their children count in one "
        "Universal Credit claim only (see uc_non_dependants_counted)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/10",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4A",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # A child is a person under 16 (WRA 2012 s.40).
        aged_16_or_over = person("age", period) >= 16
        family_member = aged_16_or_over & ~person("is_claimant_or_partner", period)
        qualifying = person("is_qualifying_young_person_for_universal_credit", period)
        # UC Regs 2013 reg 4: a person is responsible for a child or
        # qualifying young person who normally lives with them, but no one is
        # responsible for one looked after by a local authority (reg 4(6)(a)),
        # such as a foster child, unless reg 4A applies (for example (1)(c), a
        # child placed for adoption).
        responsible = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        # Sch 4 para 9(2)(g): a child or qualifying young person for whom no
        # one is responsible is not a non-dependant, in this family or
        # another.
        no_one_responsible = (
            person("is_child_for_universal_credit", period) | qualifying
        ) & ~responsible
        # Para 10(1)(b): a qualifying young person for whom the renter is
        # responsible (regs 4 and 5).
        qualifying_young_person = family_member & responsible
        # Para 10(1)(c) with para 9(2): any other member aged 16 or over is a
        # non-dependant with a bedroom, unless they head the household or are
        # the renter's foster child (para 9(2)(c), 9(3); see
        # is_lha_foster_child). The formula reads the household head
        # (is_resolved_household_head, the householder in whose name the
        # accommodation is rented) as liable to make payments on a commercial
        # basis for their occupation, so para 9(2)(d) stops them being a
        # non-dependant. A head who does not claim is not a renter either
        # (paras 1(2) and 9(1)(a)). A head who is a qualifying young person
        # the renter is responsible for keeps the para 10(1)(b) bedroom above
        # (para 9(1)(b)).
        family_non_dependant = (
            family_member
            & ~qualifying
            & ~person("is_resolved_household_head", period)
            & ~person("is_lha_foster_child", period)
        )
        family_rooms = benunit.sum(qualifying_young_person | family_non_dependant)
        # Para 9(1)(c) and 9(2): people of other families who are
        # non-dependants. A non-dependant's own child is their responsibility
        # (reg 4(2)) and so a non-dependant too; para 9(2)(g) excludes a
        # child or qualifying young person no one is responsible for, such as
        # a non-dependant's foster child.
        non_dependant = person(
            "is_non_dependant_of_household_head", period
        ) & ~no_one_responsible
        counted = benunit("uc_non_dependants_counted", period)
        # Para 10(1)(c): a non-dependant from another family who is not a
        # child.
        non_dependants = counted * benunit.max(
            person.household.sum(non_dependant & aged_16_or_over)
        )
        # Para 10(1)(d)-(f): the children in the extended benefit unit, the
        # renter's own and their non-dependants', allotted to the fewest
        # bedrooms (para 10(2)). A foster child is in no one's extended
        # benefit unit (paras 9(1)(b), 9(2)(c) and 9(3); reg 4(6)(a)).
        children = bedrooms_for_children(
            benunit,
            period,
            own_child=responsible,
            other_child=non_dependant,
            counts_other_children=counted,
        )
        # Para 10(3)(b) and para 12: additional bedrooms.
        additional = benunit("LHA_additional_bedrooms", period)
        return 1 + family_rooms + non_dependants + children + additional
