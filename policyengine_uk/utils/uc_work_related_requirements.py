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
