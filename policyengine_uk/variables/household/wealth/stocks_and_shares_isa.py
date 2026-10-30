from policyengine_uk.model_api import *


class stocks_and_shares_isa(Variable):
    label = "stocks and shares ISA holdings"
    documentation = (
        "Amount held in stocks and shares (investment) Individual Savings "
        "Accounts: stocks_and_shares_isa_balance summed over the household's "
        "members. Part of corporate_wealth, so the two must never be summed. "
        "A dataset that stores this column keeps the stored value, and "
        "projects it with corporate_wealth in every year: it is recomputed "
        "only when not stored, so a reform or situation that edits "
        "stocks_and_shares_isa_balance leaves a stored total unchanged. A "
        "household input in a situation is used for the year it is given for "
        "only."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = ["stocks_and_shares_isa_balance"]
