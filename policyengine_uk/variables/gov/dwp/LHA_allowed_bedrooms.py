from policyengine_uk.model_api import *


def child_bedrooms(boys_under_10, boys_10_to_15, girls_under_10, girls_10_to_15):
    """Bedrooms for children under 16, given counts by sex and age band.

    Children must share rooms in pairs unless they are opposite-sex and one
    is 10 or over. This is the minimum number of bedrooms that allocates them
    under those rules.
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


def bedrooms_for_children(benunit, period):
    """Bedrooms for the family's own children under 16."""
    person = benunit.members
    age = person("age", period)
    male = person("is_male", period)
    under_16 = age < 16
    under_10 = age < 10
    child_over_10 = ~under_10 & under_16
    return child_bedrooms(
        benunit.sum(under_10 & male),
        benunit.sum(child_over_10 & male),
        benunit.sum(under_10 & ~male),
        benunit.sum(child_over_10 & ~male),
    )


class LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "The number of bedrooms covered by LHA for the benefit unit"
    documentation = (
        "Universal Credit size criteria: one bedroom for the renter or "
        "couple, one for each qualifying young person the renter is "
        "responsible for, one for each other member of the benefit unit aged "
        "16 or over who is not the claimant, partner or household head (see "
        "is_benefit_unit_non_dependant_for_universal_credit, whose members "
        "also bear a housing cost contribution), one for each non-dependant "
        "aged 16 or over from another family, one for each such member of a "
        "family that makes no Universal Credit claim of its own (in the claim "
        "that counts the household's non-dependants, which also bears their "
        "contribution), and the children's bedrooms. The formula treats the "
        "household head as liable for the rent, so a head who does not claim is not a non-dependant "
        "(para 9(2)(d)); a head who is a qualifying young person the renter is "
        "responsible for keeps their bedroom. A qualifying "
        "young person no one is responsible for, such as one looked after by "
        "a local authority, is not a non-dependant and has no bedroom, in "
        "this family or another. Joint tenants and other sharers of the rent, "
        "boarders and lodgers are not non-dependants, so they add no bedroom "
        "to anyone's entitlement; the household's non-dependants count in one "
        "Universal Credit claim only (see uc_non_dependants_counted)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/10",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # A child is a person under 16 (WRA 2012 s.40).
        aged_16_or_over = person("age", period) >= 16
        family_member = aged_16_or_over & ~person("is_claimant_or_partner", period)
        qualifying = person("is_qualifying_young_person_for_universal_credit", period)
        responsible = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        # UC Regs 2013 Sch 4 para 9(2)(g): a qualifying young person for whom
        # no one is responsible (reg 4(6), such as one looked after by a local
        # authority) is not a non-dependant, in this family or another.
        no_one_responsible = qualifying & ~responsible
        # Para 10(1)(b): a qualifying young person for whom the renter is
        # responsible (regs 4 and 5).
        qualifying_young_person = family_member & responsible
        # Para 10(1)(c) with para 9(2): any other member who is not a child
        # is a non-dependant with a bedroom, unless they head the household.
        # is_benefit_unit_non_dependant_for_universal_credit marks them, and
        # uc_non_dep_deductions charges a housing cost contribution for the
        # same people (para 13), so the room and the contribution follow one
        # definition. It reads the household head (is_resolved_household_head,
        # the householder in whose name the accommodation is rented) as liable
        # to make payments on a commercial basis for their occupation, so para
        # 9(2)(d) stops them being a non-dependant. A head who does not claim
        # is not a renter either (paras 1(2) and 9(1)(a)). A head who is a
        # qualifying young person the renter is responsible for keeps the
        # para 10(1)(b) bedroom above (para 9(1)(b)).
        family_non_dependant = person(
            "is_benefit_unit_non_dependant_for_universal_credit", period
        )
        family_rooms = benunit.sum(qualifying_young_person | family_non_dependant)
        # Para 10(1)(c): a non-dependant from another family who is not a
        # child.
        other_family = person("is_non_dependant_of_household_head", period)
        non_dependant = aged_16_or_over & ~no_one_responsible & other_family
        # An in-unit non-dependant whose own family makes no Universal Credit
        # claim counts in the claim that counts the household's other
        # non-dependants (para 9(2)(f)), as in uc_non_dep_deductions, so that
        # claim has their bedroom as well as their housing cost contribution.
        # Where that claim is their own family's, family_rooms already holds
        # the bedroom.
        own_claim = (
            benunit("benunit_is_rent_liable", period)
            & benunit("is_uc_eligible", period)
            & benunit("claims_universal_credit", period)
        )
        counted = benunit("uc_non_dependants_counted", period)
        passed_on = (
            family_non_dependant & ~other_family & ~benunit.project(own_claim | counted)
        )
        non_dependants = counted * benunit.max(
            person.household.sum(non_dependant | passed_on)
        )
        return (
            1 + family_rooms + non_dependants + bedrooms_for_children(benunit, period)
        )
