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
        fixed_odds = add(
            household,
            period,
            [
                "remote_uk_horseracing_betting_net_losses",
                "land_based_fixed_odds_betting_net_losses",
                "horse_and_dog_pool_betting_net_losses",
            ],
        )
        remote = household("remote_other_betting_net_losses", period)
        financial_spread = household("financial_spread_betting_net_losses", period)
        other_spread = household("other_spread_betting_net_losses", period)
        exchange = household("betting_exchange_commission", period)
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
