from policyengine_uk.model_api import *


class lifetime_isa_balance(Variable):
    label = "Lifetime ISA balance"
    documentation = (
        "Current value of the person's Lifetime ISAs, cash and stocks and "
        "shares together. The Wealth and Assets Survey counts every ISA, "
        "Lifetime ISAs included, inside household gross financial wealth, so "
        "this is already a component of gross_financial_wealth and "
        "net_financial_wealth and must never be added to them. It is not part "
        "of savings (savings accounts) or corporate_wealth (shares, including "
        "stocks and shares ISAs), and total_wealth does not include it. Means "
        "tests count it through lifetime_isa_countable_capital, at the value "
        "left after the withdrawal charge."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
    default_value = 0
