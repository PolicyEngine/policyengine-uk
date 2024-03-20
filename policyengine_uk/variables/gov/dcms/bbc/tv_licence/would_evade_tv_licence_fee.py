from policyengine_uk.model_api import *


class would_evade_tv_licence_fee(Variable):
    label = "Would evade TV licence fee"
    documentation = (
        "Whether this household would unlawfully evade the TV licence fee."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period, parameters):
        evasion_rate = parameters(period).gov.dcms.bbc.tv_licence.evasion_rate
        return random(household) <= evasion_rate
