from policyengine_uk.model_api import *


class household_uc_reported_financial_capital(Variable):
    value_type = float
    entity = Household
    label = "Household UC capital reports consumed from the financial pool"
    documentation = (
        "Amounts consumed from the household financial proxy, counted once "
        "per benefit unit: a nonnegative complete uc_reported_capital override "
        "takes precedence over benunit_reported_capital. Without an override, "
        "use the nonnegative financial observation. A complete override "
        "replaces ordinary sources before regulation 77 company substitution, "
        "so it includes its claimant's and partner's disregarded holdings. "
        "Consume the larger of the override and those holdings after applying "
        "household_uc_company_holding_pool_scale. Each person's holding is "
        "first clipped to [0, max(0, corporate_wealth)], with positive infinity "
        "mapped to the upper bound and negative infinity to zero before any "
        "multiplication. All household holdings share "
        "one nonnegative corporate_wealth budget: if their total exceeds it, "
        "scale each person's holding proportionally before either this "
        "override floor or the separate pool deduction. This is a defensive "
        "rule for inconsistent inputs, not a statutory determination. "
        "Holdings already covered by an override "
        "must not leave the pool twice, while an override below them must not "
        "leave their remainder for another unit to count. A dependant's "
        "holding leaves the pool separately in household_uc_pool_company_holdings. "
        "Subtracting complete overrides retains the inherited residual-pool "
        "convention. The scale changes only deductions from the household "
        "pool, not regulation 77 substitution in the owner's own assessment."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        person = household.members
        financial_capital = person.benunit("benunit_reported_capital", period)
        complete_override = person.benunit("uc_reported_capital", period)
        holding = person("uc_company_holding_disregard", period)
        upper_bound = max_(0, person.household("corporate_wealth", period))
        finite_holding = np.where(
            np.isfinite(holding), holding, np.where(holding > 0, upper_bound, 0)
        )
        bounded_holdings = np.clip(finite_holding, 0, upper_bound)
        # Match the claimant holding variable's storage precision before scaling.
        own_holdings = person.benunit.sum(
            bounded_holdings * person("is_uc_claimant", period)
        ).astype(holding.dtype) * person.household(
            "household_uc_company_holding_pool_scale", period
        )
        consumed_capital = where(
            complete_override >= 0,
            max_(complete_override, own_holdings),
            financial_capital,
        )
        return household.sum(
            max_(0, consumed_capital) * person("is_benunit_head", period)
        )
