from policyengine_uk.model_api import *


class household_lifetime_isa_balance(Variable):
    label = "household Lifetime ISA balance"
    documentation = (
        "Lifetime ISA balances summed over the household's members. Like "
        "lifetime_isa_balance, it is a component of gross_financial_wealth and "
        "must never be added to it. A dataset that stores this column keeps "
        "the stored value, and the model grows the latest stored value with "
        "lifetime_isa_balance in later years, so a reform that edits "
        "lifetime_isa_balance leaves it unchanged. Balances that the data hold "
        "for a later year than the total replace it with their sum. No means "
        "test reads it."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = ["lifetime_isa_balance"]
