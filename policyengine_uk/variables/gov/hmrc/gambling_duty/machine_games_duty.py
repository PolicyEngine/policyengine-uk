from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class machine_games_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "Machine Games Duty"
    reference = "https://www.legislation.gov.uk/ukpga/2012/14/schedule/24"

    def formula_2024(household, period, parameters):
        lower = max_(household("machine_games_lower_rate_net_takings", period), 0)
        standard = max_(household("machine_games_standard_rate_net_takings", period), 0)
        higher = max_(household("machine_games_higher_rate_net_takings", period), 0)
        total = 0
        for rates, share in fiscal_year_segments(
            parameters.gov.hmrc.gambling_duty.machine_games.rates, period.start.year
        ):
            total += share * (
                lower * rates.lower + standard * rates.standard + higher * rates.higher
            )
        return total
