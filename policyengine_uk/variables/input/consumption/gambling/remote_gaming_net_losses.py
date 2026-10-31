from policyengine_uk.model_api import *


class remote_gaming_net_losses(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.gambling_duty_bases.remote_gaming"
    label = "Attributed chargeable non-exempt remote gaming losses"
    reference = "https://www.legislation.gov.uk/ukpga/2014/26/section/161"
