from policyengine_uk.model_api import *


class stocks_and_shares_isa(Variable):
    label = "stocks and shares ISA holdings"
    documentation = (
        "Amount held in stocks and shares (investment) Individual Savings Accounts: "
        "stocks_and_shares_isa_balance summed over the household's members. Part of "
        "corporate_wealth, so the two must never be summed. A dataset that stores "
        "this column keeps the stored value, and in later years the model grows the "
        "latest stored value as it grows corporate_wealth, so a reform that gives "
        "stocks_and_shares_isa_balance a formula leaves a stored total unchanged. "
        "Balances that the data hold for a later year than the total replace it with "
        "their sum. A household input in a situation applies only to its own year."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = ["stocks_and_shares_isa_balance"]
