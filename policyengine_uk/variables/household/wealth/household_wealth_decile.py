from policyengine_uk.model_api import *


class household_wealth_decile(Variable):
    label = "household wealth decile"
    documentation = (
        "Person-weighted decile of gross total_wealth, before debt deductions. "
        "Each household's weight is household_weight * household_count_people. "
        "Equal wealth values are ranked in original household/entity order. "
        "Changing this order, including when rebuilding a dataset, can change "
        "tied households' decile assignments. Negative total_wealth participates "
        "in the ranking before its output is set to -1. Household weights are "
        "indivisible, so decile bins can still be empty."
    )
    entity = Household
    definition_period = YEAR
    value_type = int

    def formula(household, period, parameters):
        wealth = household("total_wealth", period)
        count_people = household("household_count_people", period)
        household_weight = household("household_weight", period)
        # Split equal wealth in original household order without changing wealth.
        wealth_rank = np.empty(len(wealth), dtype=int)
        wealth_rank[np.argsort(wealth, kind="stable")] = np.arange(len(wealth))
        weighted_wealth = MicroSeries(
            wealth_rank, weights=household_weight * count_people
        )
        decile = weighted_wealth.decile_rank().values
        # Set negatives to -1.
        # This avoids the bottom decile summing to a negative number,
        # which would flip the % change in the interface.
        return where(wealth < 0, -1, decile)
