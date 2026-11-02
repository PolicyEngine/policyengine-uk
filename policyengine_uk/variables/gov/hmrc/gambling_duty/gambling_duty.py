from policyengine_uk.model_api import *


class gambling_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "Gambling duty"
    adds = [
        "general_betting_duty",
        "pool_betting_duty",
        "remote_gaming_duty",
        "machine_games_duty",
        "gaming_duty",
        "bingo_duty",
        "lottery_duty",
    ]
