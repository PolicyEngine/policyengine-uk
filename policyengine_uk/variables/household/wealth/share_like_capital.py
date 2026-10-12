from policyengine_uk.model_api import *

# Itemised holdings within this much of corporate_wealth are the same holdings
# rounded differently (float32 sums of the components), not extra wealth.
RELATIVE_TOLERANCE = 1e-5
ABSOLUTE_TOLERANCE = 0.01


class share_like_capital(Variable):
    label = "share-like capital"
    documentation = (
        "Share-like holdings counted by the means-test capital tests: "
        "corporate_wealth as supplied, unless its itemised components "
        "(directly_held_shares, unit_and_investment_trusts and "
        "stocks_and_shares_isa) add up to more than it, in which case their sum. "
        "So datasets that carry only corporate_wealth, or build it as the "
        "components' sum, count exactly corporate_wealth (any sign), and a "
        "household given only the components has them counted. A gap within "
        "a hundred-thousandth of corporate_wealth plus a penny is treated as "
        "rounding, so the supplied aggregate is kept. Private pension wealth is "
        "not part of it; datasets built before private pension wealth was "
        "split out of corporate_wealth still carry it here."
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
        tolerance = RELATIVE_TOLERANCE * abs(corporate_wealth) + ABSOLUTE_TOLERANCE
        exceeds = (itemised > 0) & (itemised > corporate_wealth + tolerance)
        return where(exceeds, itemised, corporate_wealth)
