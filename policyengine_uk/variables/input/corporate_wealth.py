from policyengine_uk.model_api import *


class corporate_wealth(Variable):
    label = "corporate wealth"
    documentation = (
        "Wealth held in corporations directly or through investment funds, "
        "outside pensions: directly_held_shares (UK shares and employee shares "
        "and options), unit_and_investment_trusts and stocks_and_shares_isa. "
        "Datasets that carry those components build this variable as their "
        "exact sum, so it must never be summed with any of them. Private pension "
        "wealth is carried separately in private_pension_wealth; datasets built "
        "before that split folded it into this variable."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
