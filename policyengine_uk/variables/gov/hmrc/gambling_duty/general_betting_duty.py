from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class general_betting_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "General Betting Duty"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2014/26/part/3/chapter/1",
        "https://www.legislation.gov.uk/ukpga/2026/11/section/87",
    )

    def formula_2024(household, period, parameters):
        fixed_odds = (
            max_(household("remote_uk_horseracing_betting_net_losses", period), 0)
            + max_(household("land_based_fixed_odds_betting_net_losses", period), 0)
            + max_(household("horse_and_dog_pool_betting_net_losses", period), 0)
        )
        remote = max_(household("remote_other_betting_net_losses", period), 0)
        financial_spread = max_(
            household("financial_spread_betting_net_losses", period), 0
        )
        other_spread = max_(household("other_spread_betting_net_losses", period), 0)
        exchange = max_(household("betting_exchange_commission", period), 0)
        total = 0
        for rates, share in fiscal_year_segments(
            parameters.gov.hmrc.gambling_duty.general_betting.rates, period.start.year
        ):
            total += share * (
                fixed_odds * rates.fixed_odds
                + remote * rates.remote
                + financial_spread * rates.financial_spread
                + other_spread * rates.other_spread
                + exchange * rates.exchange_commission
            )
        return total
