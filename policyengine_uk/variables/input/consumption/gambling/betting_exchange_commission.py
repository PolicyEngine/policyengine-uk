from policyengine_uk.model_api import *


class betting_exchange_commission(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    label = "Chargeable betting exchange commission attributed to the household"
    reference = "https://www.legislation.gov.uk/ukpga/2014/26/section/141"
