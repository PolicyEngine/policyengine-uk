from policyengine_uk.model_api import *


class cash_isa(Variable):
    label = "cash ISA holdings"
    documentation = (
        "Amount held in cash Individual Savings Accounts: cash_isa_balance "
        "summed over the household's members. A dataset that stores this "
        "column keeps the stored value, and the model grows the latest stored "
        "value with savings in later years, so a reform that edits "
        "cash_isa_balance leaves a stored total unchanged. Balances that the "
        "data hold for a later year than the total replace it with their sum. "
        "A household input in a situation applies only to its own year."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = ["cash_isa_balance"]
