from policyengine_uk.model_api import *


class stocks_and_shares_isa(Variable):
    label = "stocks and shares ISA holdings"
    documentation = (
        "Amount held in stocks and shares (investment) Individual Savings Accounts: "
        "stocks_and_shares_isa_balance summed over the household's members. Part of "
        "corporate_wealth, so the two must never be summed. A dataset that stores "
        "this column keeps the stored value, and the model grows the latest stored "
        "value into later years as it grows corporate_wealth. In a later year the "
        "model sums the balances instead where the data hold them for a later year "
        "than the total, or where a reform changes what stocks_and_shares_isa sums "
        "or stops stocks_and_shares_isa_balance reading its inputs. A household "
        "input in a situation applies only to its own year."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = ["stocks_and_shares_isa_balance"]
