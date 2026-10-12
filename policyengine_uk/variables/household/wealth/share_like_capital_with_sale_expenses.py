from policyengine_uk.model_api import *

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
        without = add(
            household,
            period,
            parameters(period).gov.dwp.share_like_capital.without_sale_expenses,
        )
        return where(itemised > 0, max_(0, share_like - without), share_like)
