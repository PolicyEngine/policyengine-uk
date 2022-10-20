from policyengine_uk.model_api import *


class household_owns_tv(Variable):
    label = "Owns a TV"
    documentation = "Whether this household owns a functioning colour TV."
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period, parameters):
        percent_owning_tv = parameters(
            period
        ).gov.dcms.bbc.tv_licence.tv_ownership
        return random(household) <= percent_owning_tv
