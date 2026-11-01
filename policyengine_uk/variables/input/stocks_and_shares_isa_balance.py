from policyengine_uk.model_api import *


class stocks_and_shares_isa_balance(Variable):
    label = "Stocks and shares ISA balance"
    documentation = (
        "Current value of the person's stocks and shares (investment) ISAs, "
        "Lifetime ISAs excluded (lifetime_isa_balance). The household's "
        "stocks_and_shares_isa sums it over its members, so a dataset that "
        "stores stocks_and_shares_isa itself keeps that stored total instead. "
        "Like that total, it is part of corporate_wealth, so the two must "
        "never be summed. A child's junior stocks and shares ISA is the "
        "child's own. The means tests count the balance in its holder's "
        "benefit unit, for the claimant and partner only "
        "(stocks_and_shares_isa_countable_capital)."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
    default_value = 0
