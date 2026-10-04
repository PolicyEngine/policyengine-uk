from policyengine_uk.model_api import *


class unitemised_corporate_wealth(Variable):
    label = "corporate wealth not itemised into components"
    documentation = (
        "The part of corporate_wealth not carried in its itemised components "
        "directly_held_shares, unit_and_investment_trusts and "
        "stocks_and_shares_isa, floored at nil. On datasets without the "
        "components it equals corporate_wealth (including the private pension "
        "wealth that datasets built before that split fold into it); on datasets "
        "that build corporate_wealth as the exact sum of the components it is "
        "about nil. The means-test capital sources list the components and this "
        "residual instead of corporate_wealth, so each itemised asset can carry "
        "its own valuation rule while datasets without the split keep counting "
        "corporate_wealth as before, and no holding is counted twice."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        itemised = add(
            household,
            period,
            [
                "directly_held_shares",
                "unit_and_investment_trusts",
                "stocks_and_shares_isa",
            ],
        )
        return max_(0, household("corporate_wealth", period) - itemised)
