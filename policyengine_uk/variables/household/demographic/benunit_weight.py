from policyengine_uk.model_api import *


class benunit_weight(Variable):
    value_type = float
    entity = BenUnit
    label = "Weight factor for the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.max(benunit.members("person_weight", period))
