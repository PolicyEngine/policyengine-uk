from policyengine_uk.model_api import *
from policyengine_uk.utils.tenure import is_renting_tenure


class is_renting(Variable):
    value_type = bool
    entity = Household
    label = "Is renting"
    definition_period = YEAR

    def formula(household, period, parameters):
        return is_renting_tenure(household("tenure_type", period))
