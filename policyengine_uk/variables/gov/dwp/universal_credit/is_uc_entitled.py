from policyengine_uk.model_api import *


class is_uc_entitled(Variable):
    label = "meets the means test for Universal Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        uc = benunit("universal_credit_pre_benefit_cap", period)
        return uc > 0
