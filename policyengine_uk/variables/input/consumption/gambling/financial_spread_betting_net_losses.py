from policyengine_uk.model_api import *


class financial_spread_betting_net_losses(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    label = "Attributed dutiable financial spread betting losses"
    reference = "https://www.legislation.gov.uk/ukpga/2014/26/section/128"
