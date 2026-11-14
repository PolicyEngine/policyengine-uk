from policyengine_uk.model_api import *


class household_lifetime_isa_balance(Variable):
    label = "household Lifetime ISA balance"
    documentation = (
        "Lifetime ISA balances summed over the household's members. Like "
        "lifetime_isa_balance, it is a component of gross_financial_wealth and must "
        "never be added to it. A dataset that stores this column keeps the stored "
        "value, and the model grows the latest stored value into later years as it "
        "grows lifetime_isa_balance. In a later year the model sums the balances "
        "instead where the data hold them for a later year than the total, or where "
        "a reform changes what household_lifetime_isa_balance sums or stops "
        "lifetime_isa_balance reading its inputs. No means test reads it."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    adds = ["lifetime_isa_balance"]
