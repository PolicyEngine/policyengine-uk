from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class bingo_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "Bingo Duty"
    reference = (
        "https://www.legislation.gov.uk/ukpga/1981/63/section/17/2024-04-06",
        "https://www.legislation.gov.uk/ukpga/2026/11/section/88",
    )

    def formula_2024(household, period, parameters):
        receipts = max_(household("bingo_net_receipts", period), 0)
        total = 0
        for rates, share in fiscal_year_segments(
            parameters.gov.hmrc.gambling_duty.bingo, period.start.year
        ):
            total += receipts * rates.rate * share
        return total
