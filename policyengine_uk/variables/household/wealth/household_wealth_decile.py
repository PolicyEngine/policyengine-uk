from policyengine_uk.model_api import *


def _fixed_hash(values):
    """A splitmix64 mix of integer ids: the same on every run, unlike hash()."""
    x = np.asarray(values).astype(np.int64).astype(np.uint64)
    with np.errstate(over="ignore"):
        x = x + np.uint64(0x9E3779B97F4A7C15)
        x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return x ^ (x >> np.uint64(31))


class household_wealth_decile(Variable):
    label = "household wealth decile"
    documentation = (
        "Person-weighted decile of gross total_wealth, before debt deductions. "
        "Each household's weight is household_weight * household_count_people. "
        "Equal wealth values are ranked by a fixed hash of household_id, then "
        "by row order, so tied households keep their deciles when a dataset "
        "is rebuilt in another order. Negative total_wealth participates in "
        "the ranking before its output is set to -1. Every other household "
        "gets a decile from 1 to 10, also one with zero weight. If every "
        "household has zero weight, each person counts equally. Household "
        "weights are indivisible, so decile bins can still be empty."
    )
    entity = Household
    definition_period = YEAR
    value_type = int

    def formula(household, period, parameters):
        wealth = household("total_wealth", period)
        count_people = household("household_count_people", period)
        household_weight = household("household_weight", period)
        tie_key = _fixed_hash(household("household_id", period))
        # Split equal wealth by the fixed hash, not by file order, without
        # changing wealth. np.lexsort sorts by its last key first.
        order = np.lexsort((np.arange(len(wealth)), tie_key, wealth))
        wealth_rank = np.empty(len(wealth), dtype=int)
        wealth_rank[order] = np.arange(len(wealth))
        person_weight = household_weight * count_people
        if person_weight.sum() == 0:
            # A frame with no weight at all (a test or an unweighted input)
            # still gets deciles: each person counts equally.
            person_weight = count_people
        weighted_wealth = MicroSeries(wealth_rank, weights=person_weight)
        # A zero-weight household at the start of the order would get 0.
        decile = np.clip(weighted_wealth.decile_rank().values, 1, 10)
        # Set negatives to -1.
        # This avoids the bottom decile summing to a negative number,
        # which would flip the % change in the interface.
        return where(wealth < 0, -1, decile)
