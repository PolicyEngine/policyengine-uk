from policyengine_uk.model_api import *


class bingo_net_receipts(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.gambling_duty_bases.bingo"
    label = "Attributed dutiable bingo promotion profits"
    reference = "https://www.legislation.gov.uk/ukpga/1981/63/section/17/2024-04-06"
