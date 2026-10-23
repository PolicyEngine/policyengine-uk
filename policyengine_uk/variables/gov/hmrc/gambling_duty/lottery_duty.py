from policyengine_uk.model_api import *


class lottery_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "Lottery Duty"
    reference = "https://www.legislation.gov.uk/ukpga/1993/34/section/25"

    def formula_2024(household, period, parameters):
        rate = parameters(period).gov.hmrc.gambling_duty.lottery.rate
        return household("national_lottery_ticket_spending", period) * rate
