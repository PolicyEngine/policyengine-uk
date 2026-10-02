"""The annual limits of the benefit cap.

Universal Credit and Housing Benefit apply the same four annual limits (UC
Regs 2013 reg. 80A(2); HB Regs 2006 reg. 75CA(2)), each scheme deciding for
itself who is a single claimant. Both place a claimant in Greater London by
the home they occupy (reg. 80A(3); reg. 75CA(3)).
"""

from policyengine_core.model_api import select


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
