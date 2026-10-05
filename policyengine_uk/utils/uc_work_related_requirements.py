"""Who the claimants of a Universal Credit award are.

A claim is made by a single person or jointly by the two members of a couple
(Welfare Reform Act 2012 s. 2(1)). The work-related groups of ss. 19 to 22 and
the minimum income floor of the Universal Credit Regulations 2013 reg. 62
apply to claimants.
"""


def claimants(person, period):
    """The single claimant or the joint claimants.

    The members of the couple are `is_uc_assessed_claimant`: at most two
    people in a benefit unit. A partner who cannot be a joint claimant (reg.
    3(3)) is a member of the couple but not a claimant: no work-related group
    or floor applies to them.
    """
    return person("is_uc_assessed_claimant", period) & ~person(
        "uc_is_ineligible_partner", period
    )
