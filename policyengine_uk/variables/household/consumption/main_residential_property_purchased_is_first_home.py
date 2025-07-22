from policyengine_uk.model_api import *


class main_residential_property_purchased_is_first_home(Variable):
    label = "Residential property bought is first home"
    documentation = "Whether the residential property bought this year as a main residence was as a first-time buyer."
    entity = Household
    definition_period = YEAR
    value_type = bool
    unit = GBP

    def formula(household, period, parameters):
        residential_sd = parameters(
            period
        ).gov.hmrc.stamp_duty.statistics.residential.household
        age = household.sum(
            household.members("is_household_head", period)
            * household.members("age", period)
        )
        percentage_claiming_ftbr = (
            residential_sd.first_time_buyers_relief.calc(age)
            / residential_sd.transactions_by_age.calc(age)
        )
        return random(household) < percentage_claiming_ftbr
