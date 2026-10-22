from policyengine_uk.model_api import *
from policyengine_uk.utils.capital_valuation import (
    counted_share,
    exact_amount,
    round_to_penny,
)


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
        "household_uc_company_holding_pool_scale and valuing them as "
        "corporate_wealth is valued (90% under regulation 49(1)). Each "
        "person's holding is "
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
        "pool, not regulation 77 substitution in the owner's own assessment. "
        "A recorded financial total is unvalued, so it consumes its part "
        "beyond its claimants' holdings in full and the holdings at their "
        "counted value. Like an override, a total below the holdings still "
        "consumes them, so no part of an owner's holding is left in the pool "
        "for another unit to count."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        person = household.members
        financial_capital = exact_amount(
            person.benunit("benunit_reported_capital", period)
        )
        complete_override = exact_amount(person.benunit("uc_reported_capital", period))
        holding = exact_amount(person("uc_company_holding_disregard", period))
        upper_bound = max_(
            0, exact_amount(person.household("corporate_wealth", period))
        )
        finite_holding = np.where(
            np.isfinite(holding), holding, np.where(holding > 0, upper_bound, 0)
        )
        bounded_holdings = np.clip(finite_holding, 0, upper_bound)
        own_holdings = person.benunit.sum(
            bounded_holdings * person("is_uc_claimant", period)
        ) * person.household("household_uc_company_holding_pool_scale", period)
        # The pool counts corporate_wealth, and the holdings in it, at the reg.
        # 49(1) value, rounded to the nearest penny (reg. 6(1)). A complete
        # override is a countable figure, so the holdings it must at least
        # cover are counted at that value. A recorded financial total is used
        # unvalued and holds the holdings at full value, so it consumes its
        # part beyond the holdings in full and the holdings at their counted
        # value; a total below the holdings still consumes them, so no part of
        # an owner's holding is left for another unit. The owner's own
        # assessment still takes the full holding off the report.
        p = parameters(period).gov.dwp.universal_credit.means_test.capital
        valued_holdings = round_to_penny(
            own_holdings * counted_share(p.sale_expenses, "corporate_wealth"),
            p.round_down,
        )
        consumed_capital = where(
            complete_override >= 0,
            max_(complete_override, valued_holdings),
            where(
                financial_capital >= 0,
                max_(0, financial_capital - own_holdings) + valued_holdings,
                financial_capital,
            ),
        )
        return household.sum(
            max_(0, consumed_capital) * person("is_benunit_head", period)
        )
