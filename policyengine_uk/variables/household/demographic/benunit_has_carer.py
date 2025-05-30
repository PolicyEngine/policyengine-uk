from policyengine_uk.model_api import *


class benunit_has_carer(Variable):
    value_type = bool
    entity = BenUnit
    label = "Benefit unit has a carer"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("num_carers", period) > 0
