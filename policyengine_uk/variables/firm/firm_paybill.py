from policyengine_uk.model_api import *


class firm_paybill(Variable):
    value_type = float
    entity = Firm
    label = "Firm paybill"
    documentation = "Earnings paid to the firm's employees in the year that count as Class 1 National Insurance earnings, before any employer contributions."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
