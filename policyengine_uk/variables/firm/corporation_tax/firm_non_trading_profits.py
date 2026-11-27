from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_non_trading_profits(Variable):
    value_type = float
    entity = Firm
    label = "Firm non-trading profits"
    documentation = (
        "Profits chargeable to corporation tax other than trading profits, "
        "such as non-trading loan relationship credits, property income and "
        "chargeable gains, net of their own reliefs."
    )
    definition_period = YEAR
    hidden_input = True
    unit = GBP
