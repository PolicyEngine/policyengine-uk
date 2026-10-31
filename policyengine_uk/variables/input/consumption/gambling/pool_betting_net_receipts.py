from policyengine_uk.model_api import *


class pool_betting_net_receipts(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.gambling_duty_bases.pool_betting"
    label = "Attributed dutiable non-racing pool betting net receipts"
    reference = "https://www.legislation.gov.uk/ukpga/2014/26/section/143"
