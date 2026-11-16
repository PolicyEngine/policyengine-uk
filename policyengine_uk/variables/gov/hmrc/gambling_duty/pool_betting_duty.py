from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class pool_betting_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "Pool Betting Duty"
    reference = "https://www.legislation.gov.uk/ukpga/2014/26/section/144"

    def formula_2024(household, period, parameters):
        receipts = max_(household("pool_betting_net_receipts", period), 0)
        total = 0
        for rates, share in fiscal_year_segments(
            parameters.gov.hmrc.gambling_duty.pool_betting, period.start.year
        ):
            total += receipts * rates.rate * share
        return total
