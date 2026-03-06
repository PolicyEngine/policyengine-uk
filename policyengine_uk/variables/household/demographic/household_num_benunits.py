from policyengine_uk.model_api import *


class household_num_benunits(Variable):
    value_type = int
    entity = Household
    label = "Number of benefit units"
    definition_period = YEAR
    unit = "benefit unit"

    def formula(household, period, parameters):
        return household.sum(household.members("is_benunit_head", period))
