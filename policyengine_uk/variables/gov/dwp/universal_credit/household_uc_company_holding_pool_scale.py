from policyengine_uk.model_api import *

# The capital source that holds a disregarded company holding: a holding is
# shares in a company, which have expenses of sale, so it sits in that part of
# the share-like capital the UC financial pool counts and is budgeted against it.
HOLDINGS_SOURCE = "share_like_capital_with_sale_expenses"


class household_uc_company_holding_pool_scale(Variable):
    value_type = float
    entity = Household
    label = "Share of company holdings represented in the UC household financial pool"
    documentation = (
        "Common proportional scale for disregarded company holdings when "
        "deducting them from the household financial pool. Before budgeting, "
        "clip each person's holding to [0, max(0, share_like_capital_with_sale_expenses)], mapping "
        "positive infinity to the upper bound and negative infinity to zero. "
        "Total bounded holdings "
        "share one budget of nonnegative share_like_capital_with_sale_expenses (the share-like "
        "capital the pool counts) across override "
        "floors and separate pool deductions. This allocation is independent "
        "of row order and treats holders equally. It is a defensive rule for "
        "inconsistent inputs, not a statutory determination. It does not "
        "change regulation 77 substitution in the owner's own assessment."
    )
    definition_period = YEAR
    unit = "/1"

    def formula(household, period, parameters):
        share_like = max_(0, household(HOLDINGS_SOURCE, period))
        person = household.members
        holding = person("uc_company_holding_disregard", period)
        upper_bound = max_(0, person.household(HOLDINGS_SOURCE, period))
        finite_holding = np.where(
            np.isfinite(holding), holding, np.where(holding > 0, upper_bound, 0)
        )
        holdings = household.sum(np.clip(finite_holding, 0, upper_bound))
        return where(
            holdings > 0,
            min_(1, share_like / where(holdings > 0, holdings, 1)),
            1,
        )
