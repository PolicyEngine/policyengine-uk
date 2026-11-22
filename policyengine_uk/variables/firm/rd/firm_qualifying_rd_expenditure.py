from policyengine_uk.model_api import *


class firm_qualifying_rd_expenditure(Variable):
    value_type = float
    entity = Firm
    label = "Firm qualifying research and development expenditure"
    documentation = "Qualifying research and development expenditure in the year (staff, externally provided workers, consumables, software, data and cloud costs and qualifying subcontracting), already deducted in computing trading profit."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
