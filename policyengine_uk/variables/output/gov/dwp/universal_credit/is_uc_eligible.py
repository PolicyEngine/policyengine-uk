from policyengine_uk.model_api import *


class is_uc_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for the Universal Credit"
    documentation = "Whether this family is eligible for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.any(benunit.members("is_WA_adult", period))
