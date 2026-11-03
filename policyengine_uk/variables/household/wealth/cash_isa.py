from policyengine_uk.model_api import *


class cash_isa(Variable):
    label = "cash ISA holdings"
    documentation = (
        "Amount held in cash Individual Savings Accounts: cash_isa_balance summed "
        "over the household's members. A dataset that stores this column keeps the "
        "stored value, and the model grows the latest stored value into later years "
        "as it grows savings. In a later year the model sums the balances instead "
        "where the data hold them for a later year than the total, or where a reform "
        "changes what cash_isa sums or stops cash_isa_balance reading its inputs. A "
        "household input in a situation applies only to its own year."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = ["cash_isa_balance"]
