from policyengine_uk.model_api import *

# Itemised holdings within this share of the larger of corporate_wealth and
# their sum are the same holdings rounded differently, not extra wealth.
# Simulations hold each value as float32 (24-bit significand, spacing 2^-23 of
# the value): a dataset that builds corporate_wealth as the float64 sum of
# three components and stores all four rounds each once, and the engine adds
# the three components in float32, so the two totals differ by at most about
# 2.5 units in the last place, 3e-7 of the value. 1e-6 leaves a margin of more
# than three times that and still counts any genuine excess above a millionth.
RELATIVE_TOLERANCE = 1e-6


class share_like_capital(Variable):
    label = "share-like capital"
    documentation = (
        "Share-like holdings counted by the means-test capital tests: "
        "corporate_wealth as supplied, unless its itemised components "
        "(directly_held_shares, unit_and_investment_trusts and "
        "stocks_and_shares_isa) are positive and add up to more than it by more "
        "than a millionth of the larger of the two, in which case their sum. "
        "Datasets that carry only corporate_wealth, or build it as the "
        "components' sum, therefore count exactly corporate_wealth (any sign): "
        "the millionth absorbs float32 rounding of the sum. A household given "
        "only components, with no corporate_wealth, has them counted in full. "
        "Private pension wealth is not part of it; datasets built before "
        "private pension wealth was split out of corporate_wealth still carry "
        "it here."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        corporate_wealth = household("corporate_wealth", period)
        itemised = add(
            household,
            period,
            [
                "directly_held_shares",
                "unit_and_investment_trusts",
                "stocks_and_shares_isa",
            ],
        )
        tolerance = RELATIVE_TOLERANCE * max_(abs(corporate_wealth), itemised)
        exceeds = (itemised > 0) & (itemised > corporate_wealth + tolerance)
        return where(exceeds, itemised, corporate_wealth)
