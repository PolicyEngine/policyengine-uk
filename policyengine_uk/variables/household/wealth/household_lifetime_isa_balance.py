from policyengine_uk.model_api import *


class household_lifetime_isa_balance(Variable):
    label = "household Lifetime ISA balance"
    documentation = (
        "Lifetime ISA balances summed over the household's members. Like "
        "lifetime_isa_balance, it is a component of gross_financial_wealth and "
        "must never be added to it. A dataset that stores this column keeps "
        "the stored value: it is recomputed only when not stored, so a reform "
        "or situation that edits lifetime_isa_balance leaves it unchanged. No "
        "means test reads it."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = ["lifetime_isa_balance"]
