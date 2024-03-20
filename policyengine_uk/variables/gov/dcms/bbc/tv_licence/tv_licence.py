from policyengine_uk.model_api import *


class tv_licence(Variable):
    label = "TV licence"
    documentation = "Net cost of a TV licence"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/21/section/363"
    category = TAX

    def formula(household, period, parameters):
        owns_tv = household("household_owns_tv", period)
        discount = household("tv_licence_discount", period)
        would_evade = household("would_evade_tv_licence_fee", period)
        fee = parameters(period).gov.dcms.bbc.tv_licence.colour
        return (owns_tv & ~would_evade) * fee * (1 - discount)
