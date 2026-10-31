from policyengine_uk.model_api import *


class land_based_casino_net_losses(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.gambling_duty_bases.gaming"
    label = "Attributed dutiable land-based casino gaming yield"
    reference = "https://www.legislation.gov.uk/ukpga/1997/16/section/11"
