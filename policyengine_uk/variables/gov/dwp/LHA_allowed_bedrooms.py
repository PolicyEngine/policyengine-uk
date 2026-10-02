from policyengine_uk.model_api import *
import pandas as pd
import warnings
from policyengine_core.model_api import *

warnings.filterwarnings("ignore")


def rooms_for_children(boys_under_10, older_boys, girls_under_10, older_girls):
    """The fewest bedrooms that hold children two to a room, where two
    children may share if they are of the same sex or both under 10.

    The arguments count children under 16: boys and girls under 10, and boys
    and girls aged 10 to 15.
    """
    # First, have over-10s share where possible
    over_10_rooms = (older_boys + 1) // 2 + (older_girls + 1) // 2
    # There may children over 10 still not sharing
    space_for_boy_under_10 = older_boys % 2
    space_for_girl_under_10 = older_girls % 2
    # Have those spaces filled where possible by children under 10
    left_over_boys_under_10 = max_(boys_under_10 - space_for_boy_under_10, 0)
    left_over_girls_under_10 = max_(girls_under_10 - space_for_girl_under_10, 0)
    # The remaining children must share in pairs
    under_10_rooms = (left_over_boys_under_10 + left_over_girls_under_10 + 1) // 2
    return over_10_rooms + under_10_rooms


def bedrooms_for_children(
    benunit, period, own_child=None, other_child=None, count_other=None
):
    """Bedrooms for the children under 16 in the family's size criteria.

    Children must share rooms in pairs unless they are opposite-sex and one
    is 10 or over. This is the minimum number of bedrooms that allocates them
    under those rules.

    ``own_child`` marks the family's members counted as its children (by
    default, every member under 16). ``other_child`` marks people under 16 in
    other families of the household who count in the household head's
    family's size criteria, such as a non-dependant's child; they share rooms
    with the head family's own children. ``count_other``, if given, maps a
    person mask to the number of those people counted for each family as
    occupiers outside it, in place of counting them all for the household
    head's family; it never counts the family's own members, so
    ``other_child`` may include them.
    """
    person = benunit.members
    age = person("age", period)
    male = person("is_male", period)
    under_16 = age < 16
    under_10 = age < 10
    if own_child is None:
        own_child = under_16
    own_child = own_child & under_16
    head_family = benunit.any(person("is_household_head", period))

    def count(group):
        own = benunit.sum(own_child & group)
        if other_child is None:
            return own
        others = other_child & under_16 & group
        if count_other is not None:
            return own + count_other(others)
        return own + head_family * benunit.max(person.household.sum(others))

    return rooms_for_children(
        count(under_10 & male),
        count(~under_10 & male),
        count(under_10 & ~male),
        count(~under_10 & ~male),
    )


class LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "The number of bedrooms covered by LHA for the benefit unit"
    documentation = (
        "Universal Credit size criteria for the renter's extended benefit "
        "unit: one bedroom for the renter or couple, one for each member of "
        "the benefit unit aged 16 or over who is not the claimant or partner, "
        "one for each non-dependant aged 16 or over, the children's bedrooms, "
        "and the additional bedrooms for overnight care and foster parents "
        "(see LHA_additional_bedrooms). A qualifying young person the renter "
        "is responsible for has their own bedroom; any other member aged 16 "
        "or over is a non-dependant and has one too, except a qualifying "
        "young person no one is responsible for, such as one looked after by "
        "a local authority. The children are the renter's own children and "
        "the children of the household head's non-dependants, such as a "
        "grandchild whose parent lives with the renter; they share rooms "
        "with each other. A child looked after by a local authority, such as "
        "a foster child, is no one's responsibility and has no bedroom. Joint "
        "tenants and other sharers of the rent, boarders and lodgers are not "
        "non-dependants, so neither they nor their children add a bedroom to "
        "anyone's entitlement; only the household head's family has "
        "non-dependants from other families (see "
        "is_non_dependant_of_household_head)."
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
        # UC Regs 2013 reg 4: a person is responsible for a child or
        # qualifying young person who normally lives with them, but no one is
        # responsible for one looked after by a local authority (reg 4(6)(a)),
        # such as a foster child, unless reg 4A applies (for example a child
        # placed for adoption).
        responsible = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        qualifying = person("is_qualifying_young_person_for_universal_credit", period)
        no_one_responsible = (
            person("is_child_for_universal_credit", period) | qualifying
        ) & ~responsible
        # UC Regs 2013 Sch 4 para 10(1)(b): a qualifying young person for
        # whom the renter is responsible (regs 4 and 5).
        qualifying_young_person = family_member & responsible
        # Para 10(1)(c) with para 9(2): any other member aged 16 or over is a
        # non-dependant, unless they are a qualifying young person for whom
        # no one is responsible (para 9(2)(g); reg 4(6)) or the renter's
        # foster child (para 9(2)(c), 9(3); see is_lha_foster_child).
        family_non_dependant = (
            family_member & ~qualifying & ~person("is_lha_foster_child", period)
        )
        family_rooms = benunit.sum(qualifying_young_person | family_non_dependant)
        # Para 9(1)(c) and 9(2): people of other families in the household
        # who are non-dependants of the household head's family. Para 9(2)(g)
        # excludes a child or qualifying young person no one in the extended
        # benefit unit is responsible for, such as a non-dependant's foster
        # child; a non-dependant's own child is their responsibility (reg
        # 4(2)) and so is a non-dependant too.
        non_dependant = (
            person("is_non_dependant_of_household_head", period) & ~no_one_responsible
        )
        head_family = benunit.any(person("is_household_head", period))
        # Para 10(1)(c): a non-dependant who is not a child.
        non_dependants = head_family * benunit.max(
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
        )
        # Para 10(3)(b) and para 12: additional bedrooms.
        additional = benunit("LHA_additional_bedrooms", period)
        return 1 + family_rooms + non_dependants + children + additional
