from policyengine_uk.model_api import *
from policyengine_uk.utils.tenure import is_renting_tenure


class benunit_is_renting(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether this family is renting"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return is_renting_tenure(benunit("benunit_tenure_type", period))
