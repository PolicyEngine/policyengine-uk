from policyengine_uk.model_api import *


class household_uc_company_holding_pool_scale(Variable):
    value_type = float
    entity = Household
    label = "Share of company holdings represented in the UC household financial pool"
    documentation = (
        "Common proportional scale for disregarded company holdings when "
        "deducting them from the household financial pool. Total holdings "
        "share one budget of nonnegative corporate_wealth across override "
        "floors and separate pool deductions. This allocation is independent "
        "of row order and treats holders equally. It is a defensive rule for "
        "inconsistent inputs, not a statutory determination. It does not "
        "change regulation 77 substitution in the owner's own assessment."
    )
    definition_period = YEAR
    unit = "/1"

    def formula(household, period, parameters):
        holdings = household.sum(
            household.members("uc_company_holding_disregard", period)
        )
        corporate_wealth = max_(0, household("corporate_wealth", period))
        return where(
            holdings > 0,
            min_(1, corporate_wealth / where(holdings > 0, holdings, 1)),
            1,
        )
