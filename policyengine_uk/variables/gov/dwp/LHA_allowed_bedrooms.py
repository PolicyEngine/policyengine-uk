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


def other_family_non_dependants(benunit, period):
    """People outside the family whom the Universal Credit claim that counts
    the household's non-dependants (uc_non_dependants_counted) treats as its
    non-dependants, children included.

    They are the Universal Credit non-dependants of other families
    (is_uc_non_dependant_of_household_head), less any child or qualifying
    young person no one is responsible for (UC Regs 2013 Sch 4 para 9(2)(g));
    the members whom is_benefit_unit_non_dependant_for_universal_credit
    marks in a family that neither makes a Universal Credit claim of its own
    nor counts the household's non-dependants (para 9(2)(f)), as in
    uc_non_dep_deductions; and a foster child aged 16 or 17 who is not a
    qualifying young person, in a family that does not count the household's
    non-dependants. Para 9(2)(c) takes such a foster child out of their
    foster parent's extended benefit unit only, and unless they head the
    household or pay the householder (para 9(2)(d)), no other exclusion in
    para 9(2) applies to them. Another renter's claim can count them, since
    the foster family's claim does not treat them as a non-dependant (para
    9(2)(f)). The model gives the household's non-dependants to one claim,
    though (uc_non_dependants_counted), so where that claim is the foster
    family's, no claim counts them. That gap comes from the model's routing,
    not from the law. Being under 21, they owe no housing cost contribution
    (para 16(2)(a)), so uc_non_dep_deductions needs no counterpart.
    """
    person = benunit.members
    other_family = person("is_uc_non_dependant_of_household_head", period)
    qualifying = person("is_qualifying_young_person_for_universal_credit", period)
    responsible = person(
        "is_child_or_qualifying_young_person_for_universal_credit", period
    )
    no_one_responsible = (
        person("is_child_for_universal_credit", period) | qualifying
    ) & ~responsible
    own_claim = (
        benunit("benunit_is_rent_liable", period)
        & benunit("is_uc_eligible", period)
        & benunit("claims_universal_credit", period)
    )
    counted = benunit("uc_non_dependants_counted", period)
    in_unit = person("is_benefit_unit_non_dependant_for_universal_credit", period)
    fostered = (
        person("is_lha_foster_child", period)
        & ~person("is_child_for_universal_credit", period)
        & ~qualifying
        & ~person("is_resolved_household_head", period)
        & ~person("pays_rent_to_householder", period)
    )
    passed_on = ~other_family & (
        (in_unit & ~benunit.project(own_claim | counted))
        | (fostered & ~benunit.project(counted))
    )
    return (other_family & ~no_one_responsible) | passed_on


class LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "The number of bedrooms covered by LHA for the benefit unit"
    documentation = (
        "Universal Credit size criteria for the renter's extended benefit "
        "unit: one bedroom for the renter or couple, one for each qualifying "
        "young person the renter is responsible for, one for each other "
        "member of the benefit unit aged 16 or over who is not the claimant, "
        "partner, household head or a foster child (see "
        "is_benefit_unit_non_dependant_for_universal_credit, whose members "
        "also bear a housing cost contribution), one for each non-dependant "
        "aged 16 or over from another family, one for each such member of a "
        "family that makes no Universal Credit claim of its own (in the claim "
        "that counts the household's non-dependants, which also bears their "
        "contribution), the children's bedrooms, and the additional bedrooms "
        "for overnight care and foster parents (see LHA_additional_bedrooms). "
        "The formula treats the household head as liable for the rent, so a "
        "head who does not claim is not a non-dependant (para 9(2)(d)); a "
        "head who is a qualifying young person the renter is responsible for "
        "keeps their bedroom. The children are the renter's own children and "
        "the children of the household's non-dependants, such as a grandchild "
        "whose parent lives with the renter; they share rooms with each "
        "other. A child or qualifying young person no one is responsible for, "
        "such as a foster child or another child looked after by a local "
        "authority, is not a non-dependant and has no bedroom, in this family "
        "or another; a child placed for adoption is the adopter's "
        "responsibility (reg 4A(1)(c)) and counts. A foster child aged 16 or "
        "17 who is not a qualifying young person is not a non-dependant of "
        "their foster parent (para 9(2)(c)), but the claim that counts the "
        "household's non-dependants has their bedroom unless it is the "
        "foster family's (see other_family_non_dependants). Joint tenants and other "
        "sharers of the rent, boarders and lodgers are not non-dependants, so "
        "they add no bedroom to anyone's entitlement; the household's "
        "non-dependants and their children count in one Universal Credit "
        "claim only (see uc_non_dependants_counted). A boarder's or lodger's "
        "child or qualifying young person adds none either: no one in the "
        "renter's extended benefit unit is responsible for them (see "
        "is_uc_non_dependant_of_household_head)."
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
        # Para 10(1)(c) with para 9(2): any other member who is not a child
        # is a non-dependant with a bedroom, unless they head the household
        # or are the renter's foster child (para 9(2)(c) and (3); see
        # is_lha_foster_child). is_benefit_unit_non_dependant_for_universal_credit
        # marks them, and uc_non_dep_deductions charges a housing cost
        # contribution for the same people (para 13), so the room and the
        # contribution follow one definition. It reads the household head
        # (is_resolved_household_head, the householder in whose name the
        # accommodation is rented) as liable to make payments on a commercial
        # basis for their occupation, so para 9(2)(d) stops them being a
        # non-dependant. A head who does not claim is not a renter either
        # (paras 1(2) and 9(1)(a)). A head who is a qualifying young person
        # the renter is responsible for keeps the para 10(1)(b) bedroom above
        # (para 9(1)(b)).
        family_non_dependant = person(
            "is_benefit_unit_non_dependant_for_universal_credit", period
        )
        family_rooms = benunit.sum(qualifying_young_person | family_non_dependant)
        # Para 9(1)(c) and 9(2): people of other families who are
        # non-dependants. A non-dependant's own child is their responsibility
        # (reg 4(2)) and so a non-dependant too. The Universal Credit flag
        # applies para 9(2)(g), so a boarder's or lodger's child or qualifying
        # young person gets no bedroom, and para 9(2)(f), so an adult whose
        # own family's claim counts them has their bedroom in that claim. An
        # in-unit non-dependant whose own family makes no Universal Credit
        # claim counts in the claim that counts the household's other
        # non-dependants, as in uc_non_dep_deductions, so that claim has their
        # bedroom as well as their housing cost contribution. Where that claim
        # is their own family's, family_rooms already holds the bedroom. A
        # foster child aged 16 or 17 who is not a qualifying young person
        # counts in that claim too, unless it is their foster family's (para
        # 9(2)(c)).
        counted = benunit("uc_non_dependants_counted", period)
        non_dependant = other_family_non_dependants(benunit, period)
        # Para 10(1)(c): a non-dependant from another family who is not a
        # child.
        non_dependants = counted * benunit.max(
            person.household.sum(non_dependant & aged_16_or_over)
        )
        # Para 10(1)(d)-(f): the children in the extended benefit unit, the
        # renter's own and their non-dependants', allotted to the fewest
        # bedrooms (para 10(2)). A foster child under 16 is in no one's
        # extended benefit unit (paras 9(1)(b), 9(2)(c) and (g); reg 4(6)(a)).
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
