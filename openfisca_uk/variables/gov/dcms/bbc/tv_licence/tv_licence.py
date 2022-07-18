from openfisca_uk.model_api import *


class tv_licence(Variable):
    label = "TV licence"
    documentation = "Net cost of a TV licence"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/21/section/363"

    def formula(household, period, parameters):
        owns_tv = household("household_owns_tv", period)
        discount = household("tv_licence_discount", period)
        fee = parameters(period).gov.dcms.bbc.tv_licence.colour
        return fee * owns_tv * (1 - discount)
