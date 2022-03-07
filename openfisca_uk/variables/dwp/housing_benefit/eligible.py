from openfisca_uk.model_api import *


class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for Housing Benefit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        social = benunit.any(benunit.members("in_social_housing", period))
        return social + benunit("LHA_eligible", period)