from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class machine_games_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "Machine Games Duty"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/14/schedule/24",
        "https://www.gov.uk/government/publications/budget-2026-overview-of-tax-legislation-and-rates-ootlar/budget-2026-overview-of-tax-legislation-and-rates-ootlar",
    )

    def formula_2024(household, period, parameters):
        lower = max_(household("machine_games_lower_rate_net_takings", period), 0)
        standard = max_(household("machine_games_standard_rate_net_takings", period), 0)
        higher = max_(household("machine_games_higher_rate_net_takings", period), 0)
        # Part of the standard-rate base; OOTLAR 1.50 moves it to the higher
        # rate from 1 April 2027.
        higher_stake = min_(
            max_(
                household(
                    "machine_games_standard_rate_higher_stake_net_takings", period
                ),
                0,
            ),
            standard,
        )
        machine_games = parameters.gov.hmrc.gambling_duty.machine_games
        schedule = {
            **machine_games.rates.children,
            "higher_stake_at_higher_rate": (
                machine_games.higher_stake_machines_at_higher_rate
            ),
        }
        total = 0
        for rates, share in fiscal_year_segments(schedule, period.start.year):
            higher_stake_rate = (
                rates.higher if rates.higher_stake_at_higher_rate else rates.standard
            )
            total += share * (
                lower * rates.lower
                + (standard - higher_stake) * rates.standard
                + higher_stake * higher_stake_rate
                + higher * rates.higher
            )
        return total
