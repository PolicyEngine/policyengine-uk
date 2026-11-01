from policyengine_uk.model_api import *


class remote_uk_horseracing_betting_net_losses(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    label = "Attributed dutiable remote UK horseracing fixed-odds losses"
    reference = "https://www.legislation.gov.uk/ukpga/2014/26/section/127"
