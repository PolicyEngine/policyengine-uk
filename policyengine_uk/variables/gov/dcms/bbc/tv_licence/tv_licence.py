from policyengine_uk.model_api import *


class tv_licence(Variable):
    label = "TV licence"
    documentation = "Net cost of a TV licence"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/21/section/363",
        "https://www.legislation.gov.uk/uksi/2016/704/regulation/9/made",
    )
    category = TAX

    def formula(household, period, parameters):
        licence_required = household("tv_licence_required", period)
        discount = household("tv_licence_discount", period)
        would_evade = household("would_evade_tv_licence_fee", period)
        fee = parameters(period).gov.dcms.bbc.tv_licence.colour
        return (licence_required & ~would_evade) * fee * (1 - discount)
