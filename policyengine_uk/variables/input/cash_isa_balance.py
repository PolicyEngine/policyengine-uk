from policyengine_uk.model_api import *


class cash_isa_balance(Variable):
    label = "Cash ISA balance"
    documentation = (
        "Current value of the person's cash ISAs, Lifetime ISAs excluded "
        "(lifetime_isa_balance). The household's cash_isa sums it over its "
        "members, so a dataset that stores cash_isa itself keeps that stored "
        "total instead. It is separate from savings, the household's ordinary "
        "savings."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
    default_value = 0
