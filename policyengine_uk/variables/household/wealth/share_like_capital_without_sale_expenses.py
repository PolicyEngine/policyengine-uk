from policyengine_uk.model_api import *


class share_like_capital_without_sale_expenses(Variable):
    label = "share-like capital without expenses of sale"
    documentation = (
        "The part of share_like_capital the means tests value at full value: "
        "share_like_capital less share_like_capital_with_sale_expenses. Nil "
        "for a household with no itemised holdings."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        return household("share_like_capital", period) - household(
            "share_like_capital_with_sale_expenses", period
        )
