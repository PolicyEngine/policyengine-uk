"""The annual limits of the benefit cap, and whose benefits it counts.

Universal Credit and Housing Benefit apply the same four annual limits (UC
Regs 2013 reg. 80A(2); HB Regs 2006 reg. 75CA(2)), each scheme deciding for
itself who is a single claimant. Both place a claimant in Greater London by
the home they occupy (reg. 80A(3); reg. 75CA(3)).
"""

from policyengine_core.model_api import select, where


def benefit_cap_annual_limit(benunit, period, parameters, single_claimant_rate):
    """The applicable annual limit for the single-claimant or other rate."""
    household_region = benunit.members.household("region", period)
    region = benunit.value_from_first_person(household_region)
    in_london = region == household_region.possible_values.LONDON
    cap = parameters(period).gov.dwp.benefit_cap
    return select(
        [
            single_claimant_rate & in_london,
            single_claimant_rate & ~in_london,
            ~single_claimant_rate & in_london,
            ~single_claimant_rate & ~in_london,
        ],
        [
            cap.single.in_london,
            cap.single.outside_london,
            cap.non_single.in_london,
            cap.non_single.outside_london,
        ],
    )


def benefit_cap_couple(benunit, period):
    """The single person or couple whose welfare benefits the cap counts.

    Each scheme names its own couple. For a family on Universal Credit it is
    the claimants, the members of the couple whose income the award assesses
    (is_uc_assessed_claimant): a single claimant or joint claimants, and the
    other member of a couple where one member claims as a single person
    (UC Regs 2013 reg 78(2)). Otherwise it is Housing Benefit's claimant and
    partner (is_claimant_or_partner; HB Regs 2006 regs 2(1), 75A). One total
    of welfare benefits (benefit_cap_welfare_benefits) serves both caps: a
    family receiving both awards is capped only through Universal Credit (UC
    Regs 2013 reg 80(2A); HB Regs 2006 reg 75F(1)(g)), so its total is the
    Universal Credit couple's. The two couples are the same unless
    is_uc_claimant is entered.
    """
    person = benunit.members
    on_universal_credit = benunit("universal_credit_pre_benefit_cap", period) > 0
    return where(
        benunit.project(on_universal_credit),
        person("is_uc_assessed_claimant", period),
        person("is_claimant_or_partner", period),
    )
