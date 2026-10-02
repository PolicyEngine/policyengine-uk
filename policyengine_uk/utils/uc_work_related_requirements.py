"""Who the claimants of a Universal Credit award are.

A claim is made by a single person or jointly by the two members of a couple
(Welfare Reform Act 2012 s. 2(1)). The work-related groups of ss. 19 to 22 and
the minimum income floor of the Universal Credit Regulations 2013 reg. 62
apply to claimants.
"""


def couple_members(person, period):
    """The claimant and any partner: at most two people in a benefit unit.

    Where the data flag more (an adult child in the parents' benefit unit),
    the two eldest are the couple.
    """
    age = person("age", period)
    flagged = person("is_uc_claimant", period)
    return flagged & (person.get_rank(person.benunit, -age, condition=flagged) < 2)


def claimants(person, period):
    """The single claimant or the joint claimants.

    A partner who cannot be a joint claimant (reg. 3(3)) is a member of the
    couple but not a claimant: no work-related group or floor applies to them.
    """
    return couple_members(person, period) & ~person("uc_is_ineligible_partner", period)


def other_member_of_single_claim(person, period):
    """The partner of a member of a couple who claims as a single person.

    Under reg. 3(3) the member who can claim does so as a single person. The
    other member is still in the couple, so their capital and income count
    (regs. 18(2) and 22(3)), but they are not a claimant for the rules that
    read "a claimant". A flag on a person with no claimant beside them (a
    single person, or a couple neither of whom can claim) marks no such claim.
    """
    return person("uc_is_ineligible_partner", period) & person.benunit(
        "uc_member_of_couple_claims_as_single_person", period
    )


def single_claim_in_rules_shared_with_legacy_benefits(benunit, period):
    """Whether a reg. 3(3) single claim sets the rules the model shares.

    The benefit cap rate and exceptions and the LHA shared accommodation
    test serve Housing Benefit as well as Universal Credit. Housing Benefit
    and the other legacy benefits have no single claim by a member of a
    couple, so a family claiming legacy benefits keeps the couple rules.
    """
    return benunit("uc_member_of_couple_claims_as_single_person", period) & ~benunit(
        "claims_legacy_benefits", period
    )


def other_member_of_single_claim_in_shared_rules(person, period):
    """`other_member_of_single_claim`, for the rules shared with legacy benefits."""
    return other_member_of_single_claim(person, period) & ~person.benunit(
        "claims_legacy_benefits", period
    )
