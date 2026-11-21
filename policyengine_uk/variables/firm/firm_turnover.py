from policyengine_uk.model_api import *


class firm_turnover(Variable):
    value_type = float
    entity = Firm
    label = "Firm turnover"
    documentation = (
        "Value of the firm's sales of goods and services in the year, excluding VAT."
    )
    definition_period = YEAR
    unit = GBP
