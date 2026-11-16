from policyengine_uk.model_api import *

# The share-like holdings a dataset can itemise. The formula treats a
# household as itemising only when one of these is positive, so every name in
# gov.dwp.share_like_capital.without_sale_expenses must be in this list. A
# reform that adds a holding outside it would leave a household that itemises
# only that holding with all of its share-like capital under the deduction.
# share_like_capital sums the same three names, so such a reform must add
# the holding there too.
COMPONENTS = [
    "directly_held_shares",
    "unit_and_investment_trusts",
    "stocks_and_shares_isa",
]


class share_like_capital_with_sale_expenses(Variable):
    label = "share-like capital with expenses of sale"
    documentation = (
        "The part of share_like_capital whose sale would incur expenses, so "
        "that the means tests value it less 10%: share_like_capital less the "
        "itemised holdings listed in gov.dwp.share_like_capital."
        "without_sale_expenses (unit and investment trusts, stocks and shares "
        "ISAs), floored at nil. A household with no itemised holdings has all "
        "of its share-like capital here, so datasets that carry only "
        "corporate_wealth keep the flat 10% on it."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        share_like = household("share_like_capital", period)
        itemised = add(household, period, COMPONENTS)
        # Summed from a numeric zero so that an empty list (every holding
        # taking the deduction) still works.
        without = 0 * share_like
        for variable in parameters(
            period
        ).gov.dwp.share_like_capital.without_sale_expenses:
            without = without + household(variable, period)
        return where(itemised > 0, max_(0, share_like - without), share_like)
