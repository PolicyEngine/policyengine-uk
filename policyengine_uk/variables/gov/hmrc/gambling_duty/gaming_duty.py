from policyengine_uk.model_api import *


class gaming_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "Casino Gaming Duty incidence"
    reference = (
        "https://www.legislation.gov.uk/ukpga/1997/16/section/11",
        "https://github.com/PolicyEngine/policyengine-uk/issues/2587",
    )

    def formula_2024(household, period, parameters):
        rate = parameters(period).household.consumption.gambling.casino_effective_rate
        return household("land_based_casino_net_losses", period) * rate
