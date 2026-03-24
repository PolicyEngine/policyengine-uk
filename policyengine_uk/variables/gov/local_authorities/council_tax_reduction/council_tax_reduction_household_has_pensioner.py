from policyengine_uk.model_api import *


class council_tax_reduction_household_has_pensioner(Variable):
    value_type = bool
    entity = Household
    label = "Household has a pension-age member for CTR"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household.any(household.members("is_SP_age", period))
