from policyengine_uk.model_api import *


class firm_taxable_trading_profit(Variable):
    value_type = float
    entity = Firm
    label = "Firm taxable trading profit"
    documentation = "The firm's trading profit for the year as adjusted for tax, before capital allowances, reliefs and losses. Negative for a trading loss."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
