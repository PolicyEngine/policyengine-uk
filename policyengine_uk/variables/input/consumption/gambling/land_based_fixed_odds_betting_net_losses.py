from policyengine_uk.model_api import *


class land_based_fixed_odds_betting_net_losses(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    uprating = (
        "gov.economic_assumptions.indices.obr.gambling_duty_bases.general_betting"
    )
    label = "Attributed dutiable land-based fixed-odds losses"
    reference = "https://www.legislation.gov.uk/ukpga/2014/26/section/126"
