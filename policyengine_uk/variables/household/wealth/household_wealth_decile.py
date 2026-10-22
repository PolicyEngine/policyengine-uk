from policyengine_uk.model_api import *


class household_wealth_decile(Variable):
    label = "household wealth decile"
    documentation = "Decile of wealth income (person-weighted)"
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
