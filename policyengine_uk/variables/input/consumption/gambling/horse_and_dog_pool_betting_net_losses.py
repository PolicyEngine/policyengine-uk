from policyengine_uk.model_api import *


class horse_and_dog_pool_betting_net_losses(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    label = "Attributed dutiable horse and dog racing pool losses"
    reference = "https://www.legislation.gov.uk/ukpga/2014/26/section/126"
