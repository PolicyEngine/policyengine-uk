from policyengine_uk.model_api import *


class firm_rateable_value(Variable):
    value_type = float
    entity = Firm
    label = "Firm rateable value"
    documentation = "Total rateable value of the non-domestic properties the firm occupies, as set by the Valuation Office Agency (in Scotland, the assessor). In Northern Ireland it is the net annual value set by Land and Property Services."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
