from policyengine_uk.model_api import *


class machine_games_standard_rate_net_takings(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.gambling_duty_bases.machine_games"
    label = "Attributed dutiable standard-rate machine games net takings"
    reference = "https://www.gov.uk/guidance/machine-games-duty-excise-notice-452"
