from policyengine_uk.model_api import *


class free_tv_licence_value(Variable):
    label = "free TV licence value"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/21/section/365A",
        "https://www.tvlicensing.co.uk/reducedfee",
    )

    def formula(household, period, parameters):
        owns_tv = household("household_owns_tv", period)
        discount = household("tv_licence_discount", period)
        would_evade = household("would_evade_tv_licence_fee", period)
        fee = parameters(period).gov.dcms.bbc.tv_licence.colour
        return (owns_tv & ~would_evade) * fee * discount
