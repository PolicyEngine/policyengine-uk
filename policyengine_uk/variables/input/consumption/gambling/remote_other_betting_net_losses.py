from policyengine_uk.model_api import *


class remote_other_betting_net_losses(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    uprating = (
        "gov.economic_assumptions.indices.obr.gambling_duty_bases.general_betting"
    )
    label = "Attributed dutiable other remote fixed-odds losses"
    reference = "https://www.legislation.gov.uk/ukpga/2026/11/section/87"
