from policyengine_uk.model_api import *


class firm_input_costs(Variable):
    value_type = float
    entity = Firm
    label = "Firm input costs"
    documentation = "Value of the goods and services the firm buys from other businesses in the year, excluding VAT and excluding pay and capital investment."
    definition_period = YEAR
    unit = GBP
