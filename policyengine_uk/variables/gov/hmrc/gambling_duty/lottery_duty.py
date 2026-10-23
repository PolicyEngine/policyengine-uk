from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class lottery_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "Lottery Duty"
    reference = "https://www.legislation.gov.uk/ukpga/1993/34/section/25"

    def formula_2024(household, period, parameters):
        spending = household("national_lottery_ticket_spending", period)
        total = 0
        for rates, share in fiscal_year_segments(
            parameters.gov.hmrc.gambling_duty.lottery, period.start.year
        ):
            total += spending * rates.rate * share
        return total
