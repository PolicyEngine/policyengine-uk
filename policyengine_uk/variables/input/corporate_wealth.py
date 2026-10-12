from policyengine_uk.model_api import *


class corporate_wealth(Variable):
    label = "corporate wealth"
    documentation = (
        "Wealth held in corporations directly or through investment funds: UK "
        "shares, employee shares and options, unit and investment trusts, and "
        "stocks and shares ISAs, imputed from the Wealth and Assets Survey. The "
        "stocks and shares ISA component is also exported on its own as "
        "stocks_and_shares_isa, so the two must never be summed. Private pension "
        "wealth is carried separately in private_pension_wealth; datasets built "
        "before that split folded it into this variable."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
